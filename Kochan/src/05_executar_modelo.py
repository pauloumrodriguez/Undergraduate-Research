"""Executa um perfil congelado; recusa redes que não passaram pelo gate."""
from __future__ import annotations

import argparse
import hashlib
import math
import statistics
from pathlib import Path

from model_core import gerar_passeios, preparar_amostras, sementes
from pipeline_common import (
    carregar_json,
    carregar_rede,
    gravar_csv_atomico,
    gravar_json_atomico,
    sha256_arquivo,
    sha256_json,
)


def localizar_rede(pasta: Path, ano: int):
    corrigida = pasta / f"relacoes_{ano}_corrigidas.csv"
    nova = pasta / f"relacoes_{ano}.csv"
    if corrigida.exists():
        return corrigida
    if nova.exists():
        return nova
    raise FileNotFoundError(f"Rede de {ano} não encontrada em {pasta}")


def hash_token_estavel(token: str) -> int:
    """Substitui o hash aleatório do processo usado pelo Gensim."""
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def validar_vinculo_avaliacao(redes: Path, avaliacao: dict, anos: list[int]) -> None:
    assinatura = avaliacao.get("assinatura_avaliacao")
    sem_assinatura = {
        chave: valor
        for chave, valor in avaliacao.items()
        if chave != "assinatura_avaliacao"
    }
    if not assinatura or assinatura != sha256_json(sem_assinatura):
        raise SystemExit("A avaliação não possui uma assinatura válida.")
    if Path(avaliacao["pasta_redes"]).resolve() != redes.resolve():
        raise SystemExit("A avaliação pertence a outra pasta de redes.")
    vinculo = avaliacao.get("vinculo_criptografico", {})
    esperados = vinculo.get("redes_sha256", {})
    for ano in anos:
        caminho = localizar_rede(redes, ano)
        if esperados.get(caminho.name) != sha256_arquivo(caminho):
            raise SystemExit(f"A rede de {ano} mudou depois da avaliação.")
    resumo_path = redes / "resumo_execucao.json"
    resumo_esperado = vinculo.get("resumo_execucao_sha256")
    if resumo_esperado is not None:
        if not resumo_path.exists() or sha256_arquivo(resumo_path) != resumo_esperado:
            raise SystemExit("O resumo da geração mudou depois da avaliação.")


def vetores_pares(np, embeddings, pares, operador):
    a = np.array([embeddings[x] for x, _ in pares])
    b = np.array([embeddings[y] for _, y in pares])
    if operador == "hadamard":
        return a * b
    if operador == "media":
        return (a + b) / 2
    if operador == "l1":
        return np.abs(a - b)
    if operador == "l2":
        return (a - b) ** 2
    raise ValueError(f"Operador desconhecido: {operador}")


def executar_uma(ano, repeticao, arestas, perfil):
    import numpy as np
    from gensim.models import Word2Vec
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import (
        average_precision_score,
        brier_score_loss,
        confusion_matrix,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
    )
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    seed = sementes(ano, repeticao, perfil["seed_base"])
    nos, observadas, positivas, negativas, n_componentes = preparar_amostras(
        arestas,
        seed["amostras"],
        perfil["fracao_arestas_removidas"],
        perfil["negativos"],
        perfil.get("negative_ratio"),
    )
    passeios = gerar_passeios(
        nos,
        observadas,
        arestas,
        seed["passeios"],
        perfil["num_walks"],
        perfil["walk_length"],
        perfil["p"],
        perfil["q"],
        perfil["weighted"],
    )
    modelo_embedding = Word2Vec(
        sentences=passeios,
        vector_size=perfil["dimensions"],
        window=perfil["window"],
        min_count=perfil["min_count"],
        sg=perfil["sg"],
        negative=perfil["negative"],
        hs=perfil["hs"],
        sample=perfil["sample"],
        epochs=perfil["epochs"],
        workers=perfil["workers"],
        seed=seed["word2vec"],
        hashfxn=hash_token_estavel,
    )
    embeddings = {n: modelo_embedding.wv[n] for n in nos}
    pares = positivas + negativas
    y = np.array([1] * len(positivas) + [0] * len(negativas), dtype=int)
    X = vetores_pares(np, embeddings, pares, perfil["edge_operator"])
    indices = np.arange(len(y))
    treino, teste = train_test_split(
        indices,
        test_size=perfil["test_size"],
        random_state=seed["divisao"],
        stratify=y,
    )
    regressao = LogisticRegression(
        C=perfil["logistic_C"],
        solver=perfil["logistic_solver"],
        max_iter=perfil["logistic_max_iter"],
        class_weight=perfil["class_weight"],
        random_state=seed["regressao"],
    )
    modelo = make_pipeline(StandardScaler(), regressao) if perfil["standard_scaler"] else regressao
    modelo.fit(X[treino], y[treino])
    prob = modelo.predict_proba(X[teste])[:, 1]
    y_teste = y[teste]
    auc = float(roc_auc_score(y_teste, prob))
    ap = float(average_precision_score(y_teste, prob))
    prevalencia = float(y_teste.mean())
    comum = {
        "ano": ano,
        "repeticao": repeticao,
        "nos": len(nos),
        "componentes": n_componentes,
        "arestas_originais": len(arestas),
        "arestas_observadas": len(observadas),
        "positivas_removidas": len(positivas),
        "negativas": len(negativas),
        "n_treino": len(treino),
        "n_teste": len(teste),
        "prevalencia_teste": prevalencia,
        "roc_auc": auc,
        "average_precision": ap,
        "lift_average_precision": ap / prevalencia if prevalencia else None,
        "brier": float(brier_score_loss(y_teste, prob)),
        **{f"seed_{k}": v for k, v in seed.items()},
    }
    linhas = []
    for limiar in perfil["limiares"]:
        pred = prob >= limiar
        tn, fp, fn, tp = confusion_matrix(y_teste, pred, labels=[0, 1]).ravel()
        linhas.append(
            {
                **comum,
                "limiar": limiar,
                "preditos": int(pred.sum()),
                "precisao": float(precision_score(y_teste, pred, zero_division=0)),
                "revocacao": float(recall_score(y_teste, pred, zero_division=0)),
                "f1": float(f1_score(y_teste, pred, zero_division=0)),
                "tn": int(tn),
                "fp": int(fp),
                "fn": int(fn),
                "tp": int(tp),
            }
        )
    return linhas


def resumir(resultados):
    grupos = {}
    for r in resultados:
        grupos.setdefault((r["ano"], float(r["limiar"])), []).append(r)
    metricas = [
        "roc_auc",
        "average_precision",
        "lift_average_precision",
        "brier",
        "preditos",
        "precisao",
        "revocacao",
        "f1",
    ]
    saida = []
    for (ano, limiar), linhas in sorted(grupos.items()):
        linha = {"ano": ano, "limiar": limiar, "repeticoes": len(linhas)}
        for metrica in metricas:
            valores = [float(r[metrica]) for r in linhas]
            media = statistics.fmean(valores)
            desvio = statistics.stdev(valores) if len(valores) > 1 else 0.0
            margem = 1.96 * desvio / math.sqrt(len(valores)) if valores else 0.0
            linha[f"{metrica}_media"] = media
            linha[f"{metrica}_desvio"] = desvio
            linha[f"{metrica}_ic95_inferior"] = media - margem
            linha[f"{metrica}_ic95_superior"] = media + margem
        saida.append(linha)
    return saida


def main():
    base = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz", type=Path, default=base)
    parser.add_argument("--redes", type=Path, required=True)
    parser.add_argument("--avaliacao", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=base / "config" / "modelos.json")
    parser.add_argument("--perfil", required=True)
    parser.add_argument("--anos", nargs="+", type=int, default=list(range(2006, 2011)))
    parser.add_argument("--repeticoes", type=int)
    parser.add_argument("--saida", type=Path)
    parser.add_argument("--permitir-rede-divergente", action="store_true")
    args = parser.parse_args()
    avaliacao = carregar_json(args.avaliacao)
    validar_vinculo_avaliacao(args.redes.resolve(), avaliacao, args.anos)
    rede_aprovada = avaliacao.get("gate_modelagem") == "aprovado"
    if not rede_aprovada and not args.permitir_rede_divergente:
        raise SystemExit(
            "Modelagem confirmatória bloqueada: a rede/topologia original não foi confirmada. "
            "Use --permitir-rede-divergente somente para análise exploratória."
        )
    try:
        import gensim
        import numpy
        import scipy
        import sklearn
    except ImportError as erro:
        raise SystemExit(
            "Dependências ausentes. Crie um ambiente novo e instale requirements.txt.\n"
            + str(erro)
        )
    configuracoes = carregar_json(args.config)
    if args.perfil not in configuracoes["perfis"]:
        parser.error(f"Perfil desconhecido: {args.perfil}")
    perfil = dict(configuracoes["perfis"][args.perfil])
    if args.repeticoes is not None:
        perfil["repeticoes"] = args.repeticoes
    rotulo_execucao = perfil["rotulo"] if rede_aprovada else "exploratoria_rede_divergente"
    saida = args.saida or base / "runs" / "modelos" / args.perfil
    saida.mkdir(parents=True, exist_ok=True)
    redes = {}
    hashes = {}
    for ano in args.anos:
        caminho = localizar_rede(args.redes, ano)
        redes[ano] = carregar_rede(caminho)
        hashes[caminho.name] = sha256_arquivo(caminho)
    manifesto = {
        "versao": 1,
        "perfil_id": args.perfil,
        "perfil": perfil,
        "rotulo_execucao": rotulo_execucao,
        "anos": args.anos,
        "redes_sha256": hashes,
        "avaliacao_redes_sha256": sha256_arquivo(args.avaliacao),
        "codigo_modelo_sha256": sha256_arquivo(Path(__file__).resolve()),
        "hash_tokens": "sha256_primeiros_8_bytes_little_endian",
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
        "sklearn": sklearn.__version__,
        "gensim": gensim.__version__,
    }
    manifesto["assinatura"] = sha256_json(manifesto)
    config_path = saida / "configuracao_execucao.json"
    if config_path.exists() and carregar_json(config_path) != manifesto:
        raise SystemExit("A saída já pertence a outra configuração. Escolha outra pasta.")
    gravar_json_atomico(config_path, manifesto)
    resultados = []
    for repeticao in range(1, int(perfil["repeticoes"]) + 1):
        for ano in args.anos:
            arquivo = saida / "execucoes" / f"{ano}_rep_{repeticao:03d}.json"
            if arquivo.exists():
                linhas = carregar_json(arquivo)
            else:
                linhas = executar_uma(ano, repeticao, redes[ano], perfil)
                gravar_json_atomico(arquivo, linhas)
            resultados.extend(linhas)
            print(f"{ano} repetição {repeticao}: AUC={linhas[0]['roc_auc']:.4f}", flush=True)
    gravar_csv_atomico(saida / "metricas_detalhadas.csv", list(resultados[0]), resultados)
    resumo = resumir(resultados)
    gravar_csv_atomico(saida / "resumo.csv", list(resumo[0]), resumo)
    print(f"Concluído: {saida}")


if __name__ == "__main__":
    main()
