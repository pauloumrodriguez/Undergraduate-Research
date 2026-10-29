"""Compara redes produzidas ou legadas com evidências publicadas e seus hashes."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from pipeline_common import (
    carregar_json,
    carregar_rede,
    estatisticas_rede,
    gravar_csv_atomico,
    gravar_json_atomico,
    sha256_arquivo,
    sha256_json,
)


def localizar_rede(pasta: Path, ano: int) -> Path:
    corrigida = pasta / f"relacoes_{ano}_corrigidas.csv"
    nova = pasta / f"relacoes_{ano}.csv"
    if corrigida.exists():
        return corrigida
    if nova.exists():
        return nova
    raise FileNotFoundError(f"Rede de {ano} não encontrada em {pasta}")


def rotulos_rede(caminho: Path) -> set[str] | None:
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        reader = csv.DictReader(arquivo)
        if not reader.fieldnames or not {
            "origem_rotulo",
            "destino_rotulo",
        }.issubset(reader.fieldnames):
            return None
        rotulos = set()
        for linha in reader:
            rotulos.add(linha["origem_rotulo"].strip().casefold())
            rotulos.add(linha["destino_rotulo"].strip().casefold())
        return rotulos


def main() -> None:
    base = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--redes", type=Path, required=True)
    parser.add_argument("--cumulativa", action="store_true")
    parser.add_argument("--saida", type=Path)
    parser.add_argument("--exigir-aprovacao", action="store_true")
    args = parser.parse_args()
    pasta_redes = args.redes.resolve()
    publicados = carregar_json(base / "config" / "alvos_publicados.json")
    alvos = publicados["redes"]
    resumo_path = pasta_redes / "resumo_execucao.json"
    resumo = carregar_json(resumo_path) if resumo_path.exists() else {}
    escopo_materializado = resumo.get("configuracao", {}).get(
        "escopo_temporal", "anual"
    )
    if args.cumulativa and escopo_materializado == "cumulativo_desde_2006":
        raise SystemExit(
            "Os CSVs já são cumulativos; não aplique --cumulativa uma segunda vez."
        )
    if args.cumulativa:
        modo_interpretado = "cumulativo_derivado_das_redes_anuais"
    elif escopo_materializado == "cumulativo_desde_2006":
        modo_interpretado = "cumulativo_ja_materializado_nos_csvs"
    else:
        modo_interpretado = "anual"
    saida = args.saida or pasta_redes / "avaliacao_redes.json"
    acumuladas: dict[tuple[str, str], int] = {}
    linhas = []
    hashes_redes = {}
    caminhos = {}
    for ano in range(2006, 2011):
        caminho = localizar_rede(pasta_redes, ano)
        caminhos[ano] = caminho
        hashes_redes[caminho.name] = sha256_arquivo(caminho)
        atual = carregar_rede(caminho)
        if args.cumulativa:
            acumuladas.update(atual)
            usada = acumuladas
        else:
            usada = atual
        observado = estatisticas_rede(usada)
        esperado = alvos[str(ano)]
        linha = {
            "ano": ano,
            "nos_observados": observado["nos"],
            "nos_esperados": esperado["nos"],
            "delta_nos": observado["nos"] - esperado["nos"],
            "arestas_observadas": observado["arestas"],
            "arestas_esperadas": esperado["arestas"],
            "delta_arestas": observado["arestas"] - esperado["arestas"],
        }
        linha["ano_aprovado"] = (
            linha["delta_nos"] == 0 and linha["delta_arestas"] == 0
        )
        linhas.append(linha)

    erro_relativo = sum(
        abs(linha["delta_nos"]) / linha["nos_esperados"]
        + abs(linha["delta_arestas"]) / linha["arestas_esperadas"]
        for linha in linhas
    ) / (2 * len(linhas))
    contagens_reproduzidas = all(linha["ano_aprovado"] for linha in linhas)
    provas_aprovadas = resumo.get("provas_tcc_aprovadas")
    rotulos_2006 = rotulos_rede(caminhos[2006])
    alvo_rotulos = {
        rotulo.casefold() for rotulo in publicados["nos_rede_2006_figura_6"]
    }
    nos_2006_identicos = (
        rotulos_2006 == alvo_rotulos if rotulos_2006 is not None else None
    )
    requisitos = {
        "contagens_publicadas": contagens_reproduzidas,
        "provas_binarias_tabela_3": provas_aprovadas,
        "rotulos_figura_6_2006": nos_2006_identicos,
        "topologia_original_disponivel": False,
    }
    vinculo = {
        "redes_sha256": hashes_redes,
        "resumo_execucao_sha256": (
            sha256_arquivo(resumo_path) if resumo_path.exists() else None
        ),
        "alvos_publicados_sha256": sha256_arquivo(
            base / "config" / "alvos_publicados.json"
        ),
    }
    relatorio = {
        "pasta_redes": pasta_redes.relative_to(base.resolve()).as_posix(),
        "modo": modo_interpretado,
        "escopo_materializado": escopo_materializado,
        "contagens_reproduzidas": contagens_reproduzidas,
        "erro_relativo_medio": erro_relativo,
        "provas_tcc_aprovadas": provas_aprovadas,
        "nos_2006_identicos_figura_6": nos_2006_identicos,
        "rede_identica": None,
        "motivo_rede_identica_indeterminada": (
            "As arestas originais não estão disponíveis; nem contagens nem rótulos "
            "iguais demonstram topologia ou pesos iguais."
        ),
        "requisitos_confirmatorios": requisitos,
        "vinculo_criptografico": vinculo,
        "anos": linhas,
        "gate_modelagem": "bloqueado",
        "motivo_gate": (
            "A topologia original não está disponível para confirmação. Use a opção "
            "exploratória do modelador somente com esse rótulo explícito."
        ),
    }
    relatorio["assinatura_avaliacao"] = sha256_json(relatorio)
    gravar_json_atomico(saida, relatorio)
    gravar_csv_atomico(saida.with_suffix(".csv"), list(linhas[0]), linhas)
    for linha in linhas:
        print(
            f"{linha['ano']}: {linha['nos_observados']}/{linha['arestas_observadas']} "
            f"(alvo {linha['nos_esperados']}/{linha['arestas_esperadas']})"
        )
    print(f"Gate da modelagem: {relatorio['gate_modelagem']}")
    if args.exigir_aprovacao:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
