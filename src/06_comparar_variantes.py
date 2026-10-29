"""Consolida as variantes de rede sem confundir proximidade com confirmação."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from pipeline_common import (
    carregar_json,
    gravar_csv_atomico,
    gravar_json_atomico,
)


def modo_interpretado(nome_arquivo: str, modo_relatorio: str, escopo: str) -> str:
    if nome_arquivo == "avaliacao_cumulativa.json":
        return "cumulativo_derivado_das_redes_anuais"
    if escopo == "cumulativo_desde_2006":
        return "cumulativo_ja_materializado_nos_csvs"
    return modo_relatorio


def registro_avaliacao(
    variante_id: str,
    resumo: dict,
    relatorio: dict,
    nome_arquivo: str,
    criterio: dict,
    auditoria_nos: dict,
) -> dict:
    config = resumo["configuracao"]
    provas = resumo.get("provas_tcc", [])
    falhas = []
    for prova in provas:
        if prova["aprovado"]:
            continue
        observada = prova.get("ligacao_observada")
        esperada = prova.get("ligacao_esperada")
        if observada is None:
            observada = int(int(prova.get("obtido", 0)) > 0)
        if esperada is None:
            esperada = int(int(prova.get("esperado", 0)) > 0)
        falhas.append(
            f"{prova['termo_a']} + {prova['termo_b']}: "
            f"ligação {observada} != {esperada}"
        )
    return {
        "variante": variante_id,
        "avaliacao": nome_arquivo,
        "modo_interpretado": modo_interpretado(
            nome_arquivo,
            relatorio["modo"],
            config.get("escopo_temporal", "anual"),
        ),
        "papel": criterio["papel"],
        "compatibilidade_texto": criterio["compatibilidade_texto"],
        "provas_tcc_aprovadas": bool(resumo.get("provas_tcc_aprovadas")),
        "falhas_provas_tcc": "; ".join(falhas),
        "contagens_reproduzidas": bool(relatorio["contagens_reproduzidas"]),
        "erro_relativo_medio": float(relatorio["erro_relativo_medio"]),
        "gate_modelagem": relatorio["gate_modelagem"],
        **auditoria_nos,
        "observacao": criterio["observacao"],
    }


def resumir_contagens(relatorio: dict) -> list[dict]:
    return [
        {
            "ano": linha["ano"],
            "nos": linha["nos_observados"],
            "arestas": linha["arestas_observadas"],
            "alvo_nos": linha["nos_esperados"],
            "alvo_arestas": linha["arestas_esperadas"],
        }
        for linha in relatorio["anos"]
    ]


def auditar_nos_2006(caminho_rede: Path, esperados: list[str]) -> dict:
    observados = set()
    with caminho_rede.open(encoding="utf-8-sig", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            observados.add(linha["origem_rotulo"].strip().casefold())
            observados.add(linha["destino_rotulo"].strip().casefold())
    alvo = {rotulo.casefold() for rotulo in esperados}
    faltantes = sorted(alvo - observados)
    extras = sorted(observados - alvo)
    uniao = alvo | observados
    return {
        "nos_2006_publicados": len(alvo),
        "nos_2006_observados_semanticos": len(observados),
        "nos_2006_em_comum": len(alvo & observados),
        "jaccard_nos_2006": len(alvo & observados) / len(uniao) if uniao else 1.0,
        "nos_2006_faltantes": " | ".join(faltantes),
        "nos_2006_extras": " | ".join(extras),
        "nos_2006_identicos": not faltantes and not extras,
    }


def main() -> None:
    base = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=base / "runs" / "redes")
    parser.add_argument("--saida", type=Path, default=base / "evidencias")
    args = parser.parse_args()

    criterios = carregar_json(base / "config" / "criterios_variantes.json")
    alvos = carregar_json(base / "config" / "alvos_publicados.json")
    nos_2006 = alvos["nos_rede_2006_figura_6"]
    metadados = criterios["variantes"]
    registros: list[dict] = []
    contagens: dict[str, list[dict]] = {}

    for pasta in sorted(p for p in args.runs.iterdir() if p.is_dir()):
        resumo_path = pasta / "resumo_execucao.json"
        if not resumo_path.exists():
            continue
        if pasta.name not in metadados:
            raise ValueError(f"Faltam critérios declarados para {pasta.name}")
        resumo = carregar_json(resumo_path)
        auditoria_nos = auditar_nos_2006(pasta / "relacoes_2006.csv", nos_2006)
        for avaliacao_path in sorted(pasta.glob("avaliacao*.json")):
            relatorio = carregar_json(avaliacao_path)
            chave = f"{pasta.name}/{avaliacao_path.name}"
            registros.append(
                registro_avaliacao(
                    pasta.name,
                    resumo,
                    relatorio,
                    avaliacao_path.name,
                    metadados[pasta.name],
                    auditoria_nos,
                )
            )
            contagens[chave] = resumir_contagens(relatorio)

    sem_resultado = sorted(set(metadados) - {r["variante"] for r in registros})
    if sem_resultado:
        raise ValueError(f"Variantes declaradas sem resultados: {sem_resultado}")

    ordenados = sorted(registros, key=lambda r: r["erro_relativo_medio"])
    nao_contraditos = [
        r
        for r in ordenados
        if r["provas_tcc_aprovadas"]
        and r["papel"] not in {"diagnostico", "ajuste_pos_hoc"}
    ]
    textuais = [r for r in ordenados if r["papel"] == "reconstrucao_textual"]
    exatos = [r for r in ordenados if r["contagens_reproduzidas"]]
    ajustes_pos_hoc = [r for r in ordenados if r["papel"] == "ajuste_pos_hoc"]

    if exatos:
        conclusao = (
            "Uma derivação pós-hoc reproduziu todas as contagens publicadas, mas "
            "permanece não confirmatória porque suas exclusões foram deduzidas dos "
            "próprios alvos e a topologia original não está disponível. A melhor "
            "candidata não ajustada continua sendo apenas uma hipótese."
        )
    else:
        conclusao = (
            "Nenhuma variante reproduziu as contagens publicadas. A variante mais "
            "próxima não pode ser aceita se falhar uma prova explícita, e a melhor "
            "candidata não contradita continua sendo apenas uma hipótese de "
            "reconstrução."
        )
    consolidado = {
        "politica": criterios["politica"],
        "total_avaliacoes": len(registros),
        "nenhuma_variante_reproduz_contagens": not exatos,
        "nenhuma_rede_confirmatoria": True,
        "nenhuma_variante_reproduz_nos_2006": not any(
            r["nos_2006_identicos"] for r in registros
        ),
        "gate_modelagem_global": "bloqueado",
        "variantes_com_contagens_exatas": exatos,
        "ajustes_pos_hoc": ajustes_pos_hoc,
        "reconstrucao_textual_preferencial": textuais[0] if textuais else None,
        "melhor_candidata_nao_contradita": nao_contraditos[0] if nao_contraditos else None,
        "mais_proxima_sem_filtro_de_evidencia": ordenados[0] if ordenados else None,
        "avaliacoes": ordenados,
        "contagens": contagens,
        "conclusao": conclusao,
    }
    args.saida.mkdir(parents=True, exist_ok=True)
    gravar_json_atomico(args.saida / "comparacao_variantes.json", consolidado)
    gravar_csv_atomico(
        args.saida / "comparacao_variantes.csv",
        list(registros[0]),
        ordenados,
    )
    print(f"Avaliações consolidadas: {len(registros)}")
    print(f"Gate global: {consolidado['gate_modelagem_global']}")
    if textuais:
        print(
            "Reconstrução textual: "
            f"{textuais[0]['variante']} ({textuais[0]['modo_interpretado']})"
        )
    if nao_contraditos:
        print(
            "Melhor não contradita: "
            f"{nao_contraditos[0]['variante']} "
            f"({nao_contraditos[0]['modo_interpretado']}, "
            f"erro={nao_contraditos[0]['erro_relativo_medio']:.6f})"
        )
    if ordenados:
        print(
            "Mais próxima sem filtro: "
            f"{ordenados[0]['variante']} "
            f"({ordenados[0]['modo_interpretado']}, "
            f"provas={ordenados[0]['provas_tcc_aprovadas']})"
        )


if __name__ == "__main__":
    main()
