"""Piloto de previsão temporal para as redes anuais v11."""

import argparse
from collections import defaultdict
import importlib
from itertools import combinations
from pathlib import Path
from statistics import mean, stdev
import sys


ANOS_BASE = range(2006, 2011)
HORIZONTES = (1, 3, 5)
TAMANHO_TOP = 20
PERFIL = "reconstrucao_tcc_v1"
PASTA_REDES = Path("runs/redes/v11_anual_2006_2015")


def treinar_e_prever(ano_base, repeticao, arestas, perfil, executor, nucleo):
    import numpy as np
    from gensim.models import Word2Vec
    from sklearn.base import clone
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import KFold
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    seed = nucleo.sementes(ano_base, repeticao, perfil["seed_base"])
    nos, observadas, positivas, negativas, _ = nucleo.preparar_amostras(
        arestas, seed["amostras"], perfil["fracao_arestas_removidas"],
        perfil["negativos"], perfil.get("negative_ratio"),
    )
    passeios = nucleo.gerar_passeios(
        nos, observadas, arestas, seed["passeios"], perfil["num_walks"],
        perfil["walk_length"], perfil["p"], perfil["q"], perfil["weighted"],
    )
    w2v = Word2Vec(
        sentences=passeios, vector_size=perfil["dimensions"], window=perfil["window"],
        min_count=perfil["min_count"], sg=perfil["sg"], negative=perfil["negative"],
        hs=perfil["hs"], sample=perfil["sample"], epochs=perfil["epochs"],
        workers=perfil["workers"], seed=seed["word2vec"],
        hashfxn=executor.hash_token_estavel,
    )
    embeddings = {no: w2v.wv[no] for no in nos}
    regressao = LogisticRegression(
        C=perfil["logistic_C"], solver=perfil["logistic_solver"],
        max_iter=perfil["logistic_max_iter"], class_weight=perfil["class_weight"],
        random_state=seed["regressao"],
    )
    modelo = make_pipeline(StandardScaler(), regressao) if perfil["standard_scaler"] else regressao
    candidatos = [par for par in combinations(nos, 2) if par not in arestas]
    if negativas != candidatos:
        raise ValueError("Este piloto requer o perfil que usa todos os pares ausentes como negativos.")
    x_positivas = executor.vetores_pares(np, embeddings, positivas, perfil["edge_operator"])
    x_candidatos = executor.vetores_pares(np, embeddings, candidatos, perfil["edge_operator"])
    probabilidades = np.empty(len(candidatos))
    folds = KFold(n_splits=5, shuffle=True, random_state=seed["divisao"])
    for treino, previsao in folds.split(x_candidatos):
        x = np.vstack([x_positivas, x_candidatos[treino]])
        y = [1] * len(positivas) + [0] * len(treino)
        modelo_fold = clone(modelo).fit(x, y)
        probabilidades[previsao] = modelo_fold.predict_proba(x_candidatos[previsao])[:, 1]
    return list(zip(candidatos, probabilidades, strict=True)), seed


def ocorrencias_futuras(ano_base, caminhos, io):
    primeira_ocorrencia = {}
    for ano in range(ano_base + 1, ano_base + max(HORIZONTES) + 1):
        for par in io.carregar_rede(caminhos[ano]):
            primeira_ocorrencia.setdefault(par, ano)
    return primeira_ocorrencia


def executar_repeticao(ano_base, repeticao, arestas, primeira_ocorrencia, perfil, executor, nucleo):
    previsoes, seed = treinar_e_prever(ano_base, repeticao, arestas, perfil, executor, nucleo)
    linhas = []
    for (origem, destino), prob in previsoes:
        primeiro_ano = primeira_ocorrencia.get((origem, destino))
        linhas.append({
            "origem": origem, "destino": destino, "probabilidade": float(prob),
            "primeira_ocorrencia_futura": primeiro_ano,
            **{f"ocorreu_ate_{h}_anos": int(primeiro_ano is not None and primeiro_ano <= ano_base + h)
               for h in HORIZONTES},
        })
    linhas.sort(key=lambda linha: -linha["probabilidade"])

    resumo = []
    for limiar in perfil["limiares"]:
        selecionadas = [linha for linha in linhas if linha["probabilidade"] >= limiar]
        for horizonte in HORIZONTES:
            acertos = sum(linha[f"ocorreu_ate_{horizonte}_anos"] for linha in selecionadas)
            resumo.append({
                "ano_base": ano_base, "horizonte_anos": horizonte, "limiar": limiar,
                "preditos": len(selecionadas), "acertos": acertos,
                "taxa_acerto": acertos / len(selecionadas) if selecionadas else None,
            })

    ranking = []
    top = linhas[:TAMANHO_TOP]
    for horizonte in HORIZONTES:
        campo = f"ocorreu_ate_{horizonte}_anos"
        acertos_top = sum(linha[campo] for linha in top)
        acertos_todos = sum(linha[campo] for linha in linhas)
        taxa_top = acertos_top / len(top)
        taxa_todos = acertos_todos / len(linhas)
        ranking.append({
            "ano_base": ano_base, "horizonte_anos": horizonte,
            "n_top": len(top), "acertos_top": acertos_top, "taxa_top": taxa_top,
            "n_candidatos": len(linhas), "acertos_todos": acertos_todos,
            "taxa_todos": taxa_todos,
            "razao_taxas": taxa_top / taxa_todos if taxa_todos else None,
        })
    return linhas, resumo, ranking, seed


def consolidar_ranking(ranking):
    grupos = defaultdict(list)
    for linha in ranking:
        grupos[(linha["ano_base"], linha["horizonte_anos"])].append(linha)
    resultado = []
    for (ano, horizonte), linhas in sorted(grupos.items()):
        taxas = [linha["taxa_top"] for linha in linhas]
        referencia = linhas[0]["taxa_todos"]
        resultado.append({
            "ano_base": ano, "horizonte_anos": horizonte, "repeticoes": len(linhas),
            "taxa_top_media": mean(taxas),
            "taxa_top_desvio_padrao": stdev(taxas) if len(taxas) > 1 else None,
            "taxa_top_min": min(taxas), "taxa_top_max": max(taxas),
            "taxa_todos": referencia,
            "razao_taxas_media": mean(taxas) / referencia if referencia else None,
            "rodadas_acima_referencia": sum(taxa > referencia for taxa in taxas),
        })
    return resultado


def consolidar_limiares(resumo):
    grupos = defaultdict(list)
    for linha in resumo:
        grupos[(linha["ano_base"], linha["horizonte_anos"], linha["limiar"])].append(linha)
    resultado = []
    for (ano, horizonte, limiar), linhas in sorted(grupos.items()):
        taxas = [linha["taxa_acerto"] for linha in linhas if linha["preditos"]]
        preditos = sum(linha["preditos"] for linha in linhas)
        acertos = sum(linha["acertos"] for linha in linhas)
        resultado.append({
            "ano_base": ano, "horizonte_anos": horizonte, "limiar": limiar,
            "repeticoes": len(linhas), "rodadas_com_previsao": len(taxas),
            "rodadas_sem_previsao": len(linhas) - len(taxas),
            "preditos_total": preditos, "acertos_total": acertos,
            "taxa_acerto_media_rodadas_com_previsao": mean(taxas) if taxas else None,
            "taxa_acerto_agrupada": acertos / preditos if preditos else None,
        })
    return resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projeto", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--redes", type=Path, help="Pasta dos CSVs anuais da v11 e de sua avaliação.")
    parser.add_argument("--anos", nargs="+", type=int, choices=ANOS_BASE, default=[2006])
    parser.add_argument("--repeticoes", type=int, default=1)
    parser.add_argument("--saida", type=Path)
    args = parser.parse_args()
    if args.repeticoes < 1:
        parser.error("--repeticoes deve ser maior que zero.")
    anos = sorted(set(args.anos))
    projeto = args.projeto.resolve()
    sufixo = "_".join(map(str, anos))
    if args.repeticoes > 1:
        sufixo += f"_{args.repeticoes}rep"
    saida = args.saida or projeto / "runs/modelos" / f"piloto_temporal_v11_{sufixo}"
    if saida.exists():
        parser.error(f"A pasta de saída já existe: {saida}. Indique outra com --saida.")

    sys.path.insert(0, str(projeto / "src"))
    executor = importlib.import_module("05_executar_modelo")
    nucleo = importlib.import_module("model_core")
    io = importlib.import_module("pipeline_common")

    redes = (args.redes or projeto / PASTA_REDES).resolve()
    resumo_rede = io.carregar_json(redes / "resumo_execucao.json")
    if (resumo_rede["variante_id"] != "v11_apenas_termo_principal"
            or resumo_rede["configuracao"]["escopo_temporal"] != "anual"):
        parser.error("Use os CSVs anuais da variante v11.")
    avaliacao = io.carregar_json(redes / "avaliacao_redes.json")
    executor.validar_vinculo_avaliacao(redes, avaliacao, anos, projeto)
    perfil = io.carregar_json(projeto / "config/modelos.json")["perfis"][PERFIL]

    anos_csv = sorted({ano + h for ano in anos for h in range(max(HORIZONTES) + 1)})
    caminhos = {ano: redes / f"relacoes_{ano}.csv" for ano in anos_csv}
    if faltantes := [str(path) for path in caminhos.values() if not path.is_file()]:
        parser.error("Arquivos ausentes: " + ", ".join(faltantes))
    if any(executor.localizar_rede(redes, ano) != caminhos[ano] for ano in anos):
        parser.error("A avaliação aponta para uma rede diferente do CSV anual original.")
    hashes = {path.name: io.sha256_arquivo(path) for path in caminhos.values()}
    resultados = {}
    resumo = []
    ranking = []
    sementes = {}
    for ano in anos:
        arestas = io.carregar_rede(caminhos[ano])
        primeira_ocorrencia = ocorrencias_futuras(ano, caminhos, io)
        resultados[ano] = []
        sementes[ano] = {}
        for repeticao in range(1, args.repeticoes + 1):
            linhas, por_limiar, por_ranking, sementes[ano][repeticao] = executar_repeticao(
                ano, repeticao, arestas, primeira_ocorrencia, perfil, executor, nucleo,
            )
            if args.repeticoes == 1:
                resultados[ano].extend(linhas)
            else:
                # Guarda as linhas necessárias para conferir o Top 20 e os limiares.
                menor_limiar = min(perfil["limiares"])
                resultados[ano].extend(
                    {"repeticao": repeticao, "posicao": posicao, **linha}
                    for posicao, linha in enumerate(linhas, 1)
                    if posicao <= TAMANHO_TOP or linha["probabilidade"] >= menor_limiar
                )
                for linha in por_limiar + por_ranking:
                    linha["repeticao"] = repeticao
            resumo.extend(por_limiar)
            ranking.extend(por_ranking)
            if repeticao % 10 == 0 or repeticao == args.repeticoes:
                print(f"{ano}: {repeticao}/{args.repeticoes} repetições concluídas.", flush=True)

    if hashes != {path.name: io.sha256_arquivo(path) for path in caminhos.values()}:
        raise RuntimeError("Os CSVs de entrada mudaram durante a execução.")
    saida.mkdir(parents=True, exist_ok=False)
    for ano, linhas in resultados.items():
        prefixo = "previsoes" if args.repeticoes == 1 else "pares_selecionados"
        io.gravar_csv_atomico(saida / f"{prefixo}_{ano}.csv", list(linhas[0]), linhas)
    io.gravar_csv_atomico(saida / "resumo_temporal.csv", list(resumo[0]), resumo)
    io.gravar_csv_atomico(saida / "ranking_top20.csv", list(ranking[0]), ranking)
    ranking_consolidado = consolidar_ranking(ranking)
    limiares_consolidados = consolidar_limiares(resumo)
    io.gravar_csv_atomico(saida / "ranking_top20_consolidado.csv", list(ranking_consolidado[0]), ranking_consolidado)
    io.gravar_csv_atomico(saida / "limiares_consolidados.csv", list(limiares_consolidados[0]), limiares_consolidados)
    io.gravar_json_atomico(saida / "protocolo.json", {
        "anos_base": anos, "repeticoes_por_ano": args.repeticoes, "perfil_origem": PERFIL,
        "perfil": perfil, "sementes_por_ano": sementes, "horizontes": HORIZONTES,
        "tamanho_top": TAMANHO_TOP,
        "regra": "Primeira coocorrência observada entre o ano seguinte e o ano-alvo inclusive.",
        "treino": "Amostras do ano-base. Cada grupo de pares ausentes é pontuado por um modelo treinado nos outros quatro e nas positivas ocultadas.",
        "candidatos": "Pares sem aresta no ano-base, com os dois termos ativos nesse ano.",
        "ranking": "Top 20 fixo. A taxa de referência é calculada sobre todos os candidatos do ano-base.",
        "taxas": "Rodadas sem previsões têm taxa em branco; a média por limiar usa apenas rodadas com previsões.",
        "redes_sha256": hashes,
        "script_sha256": io.sha256_arquivo(Path(__file__)),
    })
    print(f"Resultados gravados em {saida}")


if __name__ == "__main__":
    main()
