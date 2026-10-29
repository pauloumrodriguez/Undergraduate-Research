"""Explora, sem promover a confirmação, o encaixe pós-hoc da v11 na Figura 6."""
from __future__ import annotations

import argparse
import csv
import itertools
from pathlib import Path

from pipeline_common import (
    carregar_json,
    gravar_csv_atomico,
    gravar_json_atomico,
    sha256_arquivo,
    sha256_json,
)


def carregar_arestas(caminho: Path) -> dict[tuple[str, str], int]:
    arestas = {}
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            par = tuple(
                sorted(
                    (
                        linha["origem_rotulo"].strip().casefold(),
                        linha["destino_rotulo"].strip().casefold(),
                    )
                )
            )
            arestas[par] = int(linha["coocorrencias"])
    return arestas


def filtrar(
    arestas: dict[tuple[str, str], int], excluidos: set[str]
) -> dict[tuple[str, str], int]:
    return {
        par: peso
        for par, peso in arestas.items()
        if not (set(par) & excluidos)
    }


def estatisticas(arestas: dict[tuple[str, str], int]) -> dict[str, int]:
    nos = {no for par in arestas for no in par}
    return {"nos": len(nos), "arestas": len(arestas)}


def main() -> None:
    base = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--redes-v11",
        type=Path,
        default=base / "runs" / "redes" / "v11_apenas_termo_principal",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=base / "evidencias" / "diagnostico_pos_hoc_figura6.json",
    )
    parser.add_argument("--exportar-v13", action="store_true")
    parser.add_argument(
        "--saida-v13",
        type=Path,
        default=base / "runs" / "redes" / "v13_ajuste_pos_hoc_exato",
    )
    args = parser.parse_args()
    publicados_path = base / "config" / "alvos_publicados.json"
    publicados = carregar_json(publicados_path)
    alvo_2006 = {
        rotulo.casefold() for rotulo in publicados["nos_rede_2006_figura_6"]
    }
    anuais = {}
    hashes = {}
    for ano in range(2006, 2011):
        caminho = args.redes_v11 / f"relacoes_{ano}.csv"
        anuais[ano] = carregar_arestas(caminho)
        hashes[caminho.name] = sha256_arquivo(caminho)

    nos_v11_2006 = {no for par in anuais[2006] for no in par}
    extras_2006 = nos_v11_2006 - alvo_2006
    faltantes_2006 = alvo_2006 - nos_v11_2006
    acumuladas = {}
    apos_excluir_extras = {}
    for ano in range(2006, 2011):
        acumuladas.update(anuais[ano])
        rede = filtrar(acumuladas, extras_2006)
        observado = estatisticas(rede)
        alvo = publicados["redes"][str(ano)]
        apos_excluir_extras[str(ano)] = {
            **observado,
            "alvo_nos": int(alvo["nos"]),
            "alvo_arestas": int(alvo["arestas"]),
            "exato": observado
            == {"nos": int(alvo["nos"]), "arestas": int(alvo["arestas"])},
        }

    uniao_2010 = {no for par in acumuladas for no in par}
    candidatos = sorted(uniao_2010 - alvo_2006 - extras_2006)
    pares_que_encaixam = []
    for par in itertools.combinations(candidatos, 2):
        excluidos = extras_2006 | set(par)
        uniao = {}
        resultados = {}
        todos_exatos = True
        for ano in range(2006, 2011):
            uniao.update(anuais[ano])
            observado = estatisticas(filtrar(uniao, excluidos))
            alvo = publicados["redes"][str(ano)]
            exato = observado == {
                "nos": int(alvo["nos"]),
                "arestas": int(alvo["arestas"]),
            }
            resultados[str(ano)] = {**observado, "exato": exato}
            todos_exatos &= exato
        if todos_exatos:
            pares_que_encaixam.append(
                {"exclusoes_adicionais": list(par), "resultados": resultados}
            )

    relatorio = {
        "natureza": "diagnostico_pos_hoc_nao_confirmatorio",
        "fonte": "Figura 6 do TCC e contagens da Tabela 6",
        "variante_base": "v11_apenas_termo_principal",
        "modo": "cumulativo_derivado",
        "hashes_redes_fonte": hashes,
        "alvos_publicados_sha256": sha256_arquivo(publicados_path),
        "nos_publicados_2006": len(alvo_2006),
        "nos_v11_2006": len(nos_v11_2006),
        "nos_publicados_faltantes_na_v11": sorted(faltantes_2006),
        "extras_v11_2006": sorted(extras_2006),
        "resultado_apos_excluir_so_extras_2006": apos_excluir_extras,
        "conjuntos_adicionais_que_encaixam_todos_os_totais": pares_que_encaixam,
        "conclusao": (
            "A exclusão dos seis extras reproduz 2006–2008; três pares diferentes "
            "de exclusões adicionais reproduzem também 2009–2010. Como TCC e artigo "
            "não permitem escolher entre eles, qualquer seleção seria ajuste pós-hoc, "
            "não reconstrução confirmada."
        ),
    }
    gravar_json_atomico(args.saida, relatorio)
    print(f"Extras em 2006: {len(extras_2006)}")
    print(f"Pares adicionais com encaixe total: {len(pares_que_encaixam)}")
    print(f"Relatório: {args.saida}")
    if args.exportar_v13:
        if len(pares_que_encaixam) != 1:
            raise SystemExit(
                "A exportação exige exatamente um conjunto adicional que encaixe todos os anos."
            )
        adicionais = set(pares_que_encaixam[0]["exclusoes_adicionais"])
        excluidos = extras_2006 | adicionais
        args.saida_v13.mkdir(parents=True, exist_ok=True)
        acumuladas_registros = {}
        resumos = []
        for ano in range(2006, 2011):
            caminho = args.redes_v11 / f"relacoes_{ano}.csv"
            with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
                for linha in csv.DictReader(arquivo):
                    if (
                        linha["origem_rotulo"].strip().casefold() in excluidos
                        or linha["destino_rotulo"].strip().casefold() in excluidos
                    ):
                        continue
                    par = tuple(sorted((linha["origem"], linha["destino"])))
                    if par not in acumuladas_registros:
                        acumuladas_registros[par] = dict(linha)
                        acumuladas_registros[par]["coocorrencias"] = 0
                    acumuladas_registros[par]["coocorrencias"] += int(
                        linha["coocorrencias"]
                    )
            linhas = list(acumuladas_registros.values())
            gravar_csv_atomico(
                args.saida_v13 / f"relacoes_{ano}.csv",
                [
                    "origem",
                    "destino",
                    "coocorrencias",
                    "origem_rotulo",
                    "destino_rotulo",
                    "origem_linha",
                    "destino_linha",
                ],
                linhas,
            )
            nos = {
                no
                for linha in linhas
                for no in (linha["origem"], linha["destino"])
            }
            resumos.append(
                {
                    "ano": ano,
                    "nos": len(nos),
                    "arestas": len(linhas),
                    "peso_total": sum(int(l["coocorrencias"]) for l in linhas),
                }
            )
        gravar_csv_atomico(
            args.saida_v13 / "resumo_redes.csv", list(resumos[0]), resumos
        )
        provas = []
        pares_finais_2006 = {
            tuple(
                sorted(
                    (
                        linha["origem_rotulo"].strip().casefold(),
                        linha["destino_rotulo"].strip().casefold(),
                    )
                )
            )
            for linha in csv.DictReader(
                (args.saida_v13 / "relacoes_2006.csv").open(
                    encoding="utf-8-sig", newline=""
                )
            )
        }
        for prova in publicados["provas_ligacao_2006"]:
            par = tuple(
                sorted((prova["termo_a"].casefold(), prova["termo_b"].casefold()))
            )
            observada = int(par in pares_finais_2006)
            provas.append(
                {
                    **prova,
                    "ligacao_observada": observada,
                    "aprovado": observada == int(prova["ligacao_esperada"]),
                }
            )
        base_resumo = carregar_json(args.redes_v11 / "resumo_execucao.json")
        derivacao = {
            "natureza": "ajuste_pos_hoc_nao_confirmatorio",
            "base": str(args.redes_v11.resolve()),
            "hashes_base": hashes,
            "exclusoes": sorted(excluidos),
            "regra_temporal": "uniao_cumulativa_com_soma_dos_pesos_anuais",
            "aviso": "As exclusões foram deduzidas dos alvos publicados; não são instrução do TCC/artigo.",
        }
        resumo_final = {
            "variante_id": "v13_ajuste_pos_hoc_exato",
            "assinatura": sha256_json(derivacao),
            "fingerprint_evidencia": base_resumo.get(
                "fingerprint_evidencia", base_resumo.get("fingerprint_indice")
            ),
            "configuracao": {
                "descricao": "Ajuste pós-hoc exato derivado de v11; proibido como confirmação.",
                "escopo_temporal": "cumulativo_desde_2006",
                "aliases_utilizados": "somente_primeiro",
                "exclusoes_pos_hoc": sorted(excluidos),
            },
            "derivacao": derivacao,
            "redes": resumos,
            "semantica_provas_tcc": publicados["semantica_provas_ligacao_2006"],
            "provas_tcc": provas,
            "provas_tcc_aprovadas": all(p["aprovado"] for p in provas),
        }
        gravar_json_atomico(args.saida_v13 / "resumo_execucao.json", resumo_final)
        print(f"v13 pós-hoc exportada: {args.saida_v13}")


if __name__ == "__main__":
    main()
