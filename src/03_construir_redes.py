"""Constrói redes experimentais com vocabulário, consultas e índice identificados."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import itertools
import string
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pipeline_common import (
    carregar_json,
    gravar_csv_atomico,
    gravar_json_atomico,
    sha256_arquivo,
    sha256_json,
)


LOCAL = threading.local()
TRADUTOR_PONTUACAO = str.maketrans("", "", string.punctuation)
ESPECIAIS_LUCENE = set("+-!(){}[]^\"~*?:\\/")


def normalizar_alias(alias: str, modo: str) -> str:
    alias = " ".join(alias.strip().split())
    if modo == "preservar":
        return alias
    if modo == "remover_pontuacao_ascii":
        return " ".join(alias.translate(TRADUTOR_PONTUACAO).split())
    raise ValueError(f"Normalização desconhecida: {modo}")


def carregar_conceitos(caminho: Path, variante: dict):
    conceitos = []
    vistos = {}
    auditoria = {"linhas": 0, "sinonimos_repetidos": [], "conceitos_duplicados": [], "aliases_compartilhados": {}}
    for numero, linha in enumerate(caminho.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not linha.strip():
            continue
        auditoria["linhas"] += 1
        partes = [normalizar_alias(p, variante["normalizacao_termos"]) for p in linha.split(";")]
        if any(not p for p in partes):
            raise ValueError(f"Linha {numero}: alias vazio após normalização")
        aliases = list(dict.fromkeys(partes))
        if len(aliases) != len(partes):
            auditoria["sinonimos_repetidos"].append(numero)
        chave = tuple(sorted(a.casefold() for a in aliases))
        if variante["duplicatas"] == "deduplicar_conceitos" and chave in vistos:
            auditoria["conceitos_duplicados"].append(
                {"linha": numero, "duplicata_de": vistos[chave]}
            )
            continue
        vistos.setdefault(chave, numero)
        rotulo = aliases[0]
        if variante["duplicatas"] == "manter_posicoes":
            no = f"T{numero:03d}|{';'.join(aliases)}"
        elif variante["duplicatas"] == "deduplicar_conceitos":
            no = ";".join(aliases)
        else:
            raise ValueError(f"Política de duplicatas desconhecida: {variante['duplicatas']}")
        conceitos.append({"linha": numero, "no": no, "rotulo": rotulo, "aliases": aliases})

    aliases_utilizados = variante.get("aliases_utilizados", "todos")
    if aliases_utilizados == "somente_primeiro":
        for conceito in conceitos:
            conceito["aliases"] = conceito["aliases"][:1]
    elif aliases_utilizados != "todos":
        raise ValueError(f"Política de aliases utilizados desconhecida: {aliases_utilizados}")
    auditoria["aliases_utilizados"] = aliases_utilizados

    mapa_alias = {}
    for conceito in conceitos:
        for alias in conceito["aliases"]:
            mapa_alias.setdefault(alias.casefold(), []).append(conceito["no"])
    compartilhados = {a: nos for a, nos in mapa_alias.items() if len(nos) > 1}
    auditoria["aliases_compartilhados"] = compartilhados
    if variante["aliases_compartilhados"] == "remover":
        mantidos = []
        removidos_sem_alias = []
        for conceito in conceitos:
            conceito["aliases"] = [
                a for a in conceito["aliases"] if a.casefold() not in compartilhados
            ]
            if not conceito["aliases"]:
                removidos_sem_alias.append(conceito["linha"])
            else:
                mantidos.append(conceito)
        conceitos = mantidos
        auditoria["conceitos_removidos_sem_alias"] = removidos_sem_alias
    elif variante["aliases_compartilhados"] != "preservar":
        raise ValueError(
            f"Política de aliases desconhecida: {variante['aliases_compartilhados']}"
        )
    auditoria["conceitos_finais"] = len(conceitos)
    auditoria["pares"] = len(conceitos) * (len(conceitos) - 1) // 2
    return conceitos, auditoria


def escapar_token(token: str) -> str:
    return "".join("\\" + c if c in ESPECIAIS_LUCENE else c for c in token)


def consulta_alias(alias: str, modo: str) -> str:
    if modo == "frase_exata":
        valor = alias.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{valor}"'
    if modo == "tokens_and":
        tokens = [escapar_token(t) for t in alias.split()]
        return "(" + " AND ".join(tokens) + ")"
    raise ValueError(f"Modo de consulta desconhecido: {modo}")


def consulta_conceito_campo(conceito: dict, modo: str, campo: str) -> str:
    partes = []
    for alias in conceito["aliases"]:
        valor = consulta_alias(alias, modo)
        partes.append(f"{campo}:{valor}")
    return "(" + " OR ".join(partes) + ")"


def consulta_conceito(conceito: dict, modo: str) -> str:
    return (
        "("
        + consulta_conceito_campo(conceito, modo, "Title")
        + " OR "
        + consulta_conceito_campo(conceito, modo, "Abstract")
        + ")"
    )


def filtros_par(conceito_a: dict, conceito_b: dict, variante: dict) -> list[str]:
    modo = variante["modo_consulta"]
    campos = variante.get("campos", "qualquer_campo")
    if campos == "qualquer_campo":
        return [consulta_conceito(conceito_a, modo), consulta_conceito(conceito_b, modo)]
    titulo_a = consulta_conceito_campo(conceito_a, modo, "Title")
    titulo_b = consulta_conceito_campo(conceito_b, modo, "Title")
    resumo_a = consulta_conceito_campo(conceito_a, modo, "Abstract")
    resumo_b = consulta_conceito_campo(conceito_b, modo, "Abstract")
    if campos == "mesmo_campo":
        return [f"(({titulo_a} AND {titulo_b}) OR ({resumo_a} AND {resumo_b}))"]
    if campos == "apenas_title":
        return [titulo_a, titulo_b]
    if campos == "apenas_abstract":
        return [resumo_a, resumo_b]
    raise ValueError(f"Política de campos desconhecida: {campos}")


def sessao_requests():
    import requests

    if not hasattr(LOCAL, "session"):
        LOCAL.session = requests.Session()
    return LOCAL.session


def parse_facet_year(valor) -> dict[str, int]:
    if isinstance(valor, dict):
        return {str(k): int(v) for k, v in valor.items()}
    if isinstance(valor, list) and len(valor) % 2 == 0:
        return {str(valor[i]): int(valor[i + 1]) for i in range(0, len(valor), 2)}
    raise ValueError(f"Formato inesperado de faceta Year: {type(valor).__name__}")


def consultar_filtros(select_url, filtros, anos, solr):
    params = [
        ("q", "*:*"),
        ("fq", f"Year:[{min(anos)} TO {max(anos)}]"),
        ("rows", 0),
        ("facet", "true"),
        ("facet.field", "Year"),
        ("facet.limit", -1),
        ("facet.mincount", 0),
        ("wt", "json"),
    ]
    params[1:1] = [("fq", filtro) for filtro in filtros]
    ultimo = None
    for tentativa in range(1, int(solr["tentativas"]) + 1):
        try:
            resposta = sessao_requests().get(
                select_url,
                params=params,
                timeout=float(solr["timeout_segundos"]),
            )
            resposta.raise_for_status()
            dados = resposta.json()
            faceta = parse_facet_year(dados["facet_counts"]["facet_fields"]["Year"])
            return {str(ano): int(faceta.get(str(ano), 0)) for ano in anos}
        except Exception as erro:
            ultimo = erro
            if tentativa < int(solr["tentativas"]):
                time.sleep(2 ** (tentativa - 1))
    raise RuntimeError(f"Consulta Solr falhou: {ultimo}")


def obter_json_solr(url, params, solr):
    ultimo = None
    for tentativa in range(1, int(solr["tentativas"]) + 1):
        try:
            resposta = sessao_requests().get(
                url, params=params, timeout=float(solr["timeout_segundos"])
            )
            resposta.raise_for_status()
            return resposta.json()
        except Exception as erro:
            ultimo = erro
            if tentativa < int(solr["tentativas"]):
                time.sleep(2 ** (tentativa - 1))
    raise RuntimeError(f"Consulta Solr falhou: {ultimo}")


def sem_response_header(valor):
    if isinstance(valor, dict):
        return {
            chave: sem_response_header(conteudo)
            for chave, conteudo in valor.items()
            if chave != "responseHeader"
        }
    if isinstance(valor, list):
        return [sem_response_header(item) for item in valor]
    return valor


def validar_solr_vivo(select_url: str, snapshot: dict, solr: dict) -> None:
    """Evita aplicar um checkpoint a uma coleção viva diferente do snapshot."""
    anos = sorted(int(ano) for ano in snapshot["por_ano"])
    contagens = consultar_filtros(select_url, [], anos, solr)
    esperado = {str(ano): int(snapshot["por_ano"][str(ano)]) for ano in anos}
    if contagens != esperado:
        raise SystemExit("O Solr vivo diverge das contagens anuais do snapshot.")

    for documentos in snapshot.get("amostras", {}).values():
        for documento in documentos:
            dados = obter_json_solr(
                select_url,
                {
                    "q": f'id:"{documento["id"]}"',
                    "rows": 2,
                    "fl": "id,Title,Abstract,Year",
                    "wt": "json",
                },
                solr,
            )["response"]["docs"]
            if dados != [documento]:
                raise SystemExit(
                    f'O documento-amostra {documento["id"]} diverge do snapshot.'
                )

    if snapshot.get("fingerprint_evidencia"):
        colecao_url = select_url.rsplit("/select", 1)[0]
        schema_vivo = sem_response_header(
            obter_json_solr(f"{colecao_url}/schema", {"wt": "json"}, solr)
        )
        config_viva = sem_response_header(
            obter_json_solr(f"{colecao_url}/config", {"wt": "json"}, solr)
        )
        if schema_vivo != snapshot["schema"] or config_viva != snapshot["config"]:
            raise SystemExit("Schema/config do Solr vivo divergem do snapshot v2.")
        for nome, registro in snapshot.get("recursos_configset", {}).items():
            resposta = sessao_requests().get(
                f"{colecao_url}/admin/file",
                params={"file": nome},
                timeout=float(solr["timeout_segundos"]),
            )
            resposta.raise_for_status()
            digest = hashlib.sha256(resposta.content).hexdigest()
            if digest != registro["sha256"]:
                raise SystemExit(f"O recurso Solr {nome} diverge do snapshot v2.")
    print("Solr vivo confere com a evidência capturada.")


def exportar_redes(saida: Path, resultados: list[dict], conceitos_por_no: dict, anos, escopo):
    resumos = []
    for ano in anos:
        linhas = []
        for r in resultados:
            if escopo == "anual":
                peso = int(r["contagens"][str(ano)])
            else:
                peso = sum(int(r["contagens"][str(a)]) for a in anos if a <= ano)
            if peso <= 0:
                continue
            ca, cb = conceitos_por_no[r["origem"]], conceitos_por_no[r["destino"]]
            linhas.append(
                {
                    "origem": r["origem"],
                    "destino": r["destino"],
                    "coocorrencias": peso,
                    "origem_rotulo": ca["rotulo"],
                    "destino_rotulo": cb["rotulo"],
                    "origem_linha": ca["linha"],
                    "destino_linha": cb["linha"],
                }
            )
        gravar_csv_atomico(
            saida / f"relacoes_{ano}.csv",
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
        nos = {n for r in linhas for n in (r["origem"], r["destino"])}
        resumos.append(
            {"ano": ano, "nos": len(nos), "arestas": len(linhas), "peso_total": sum(r["coocorrencias"] for r in linhas)}
        )
    gravar_csv_atomico(saida / "resumo_redes.csv", list(resumos[0]), resumos)
    return resumos


def avaliar_provas_ligacao(caminho_rede: Path, provas: list[dict]) -> list[dict]:
    """Compara presença/ausência de arestas com a Tabela 3 do TCC.

    A coluna ``Ligação`` da tabela é uma classe binária. Ela não informa a
    quantidade de documentos recuperados pelo Solr.
    """
    pesos_por_par: dict[tuple[str, str], list[int]] = {}
    with caminho_rede.open(encoding="utf-8-sig", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            a = linha["origem_rotulo"].strip().casefold()
            b = linha["destino_rotulo"].strip().casefold()
            par = tuple(sorted((a, b)))
            pesos_por_par.setdefault(par, []).append(int(linha["coocorrencias"]))
    avaliadas = []
    for prova in provas:
        par = tuple(
            sorted((prova["termo_a"].casefold(), prova["termo_b"].casefold()))
        )
        pesos = pesos_por_par.get(par, [])
        observada = int(bool(pesos))
        esperada = int(prova["ligacao_esperada"])
        avaliadas.append(
            {
                **prova,
                "ligacao_observada": observada,
                "pesos_registros_encontrados": pesos,
                "aprovado": observada == esperada,
            }
        )
    return avaliadas


def main():
    base = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz", type=Path, default=base)
    parser.add_argument("--config", type=Path, default=base / "config" / "variantes_rede.json")
    parser.add_argument("--variante", required=True)
    parser.add_argument("--anos", nargs="+", type=int, default=list(range(2006, 2011)))
    parser.add_argument(
        "--snapshot-solr",
        type=Path,
        default=base / "evidencias" / "solr_snapshot_v2.json",
    )
    parser.add_argument("--saida", type=Path)
    parser.add_argument("--somente-validar", action="store_true")
    args = parser.parse_args()
    if not args.anos or any(a < 2006 or a > 2015 for a in args.anos):
        parser.error("Anos permitidos: 2006–2015")
    anos = sorted(set(args.anos))
    config = carregar_json(args.config)
    if args.variante not in config["variantes"]:
        parser.error(f"Variante inexistente: {args.variante}")
    variante = config["variantes"][args.variante]
    termos_path = args.raiz.resolve() / config["termos"]
    conceitos, auditoria = carregar_conceitos(termos_path, variante)
    saida = args.saida or base / "runs" / "redes" / args.variante
    saida.mkdir(parents=True, exist_ok=True)
    gravar_json_atomico(saida / "auditoria_vocabulario.json", auditoria)
    print(f"{auditoria['conceitos_finais']} conceitos; {auditoria['pares']} pares")
    if args.somente_validar:
        return

    if not args.snapshot_solr.exists():
        raise SystemExit("Snapshot Solr ausente. Execute primeiro 02_validar_solr.py.")
    snapshot = carregar_json(args.snapshot_solr)
    if not snapshot.get("aprovado"):
        raise SystemExit("O snapshot Solr não foi aprovado.")
    solr = config["solr"]
    if snapshot.get("colecao") != solr["colecao"]:
        raise SystemExit("A coleção do snapshot difere da configuração.")
    select_url = f"{solr['base_url'].rstrip('/')}/{solr['colecao']}/select"
    validar_solr_vivo(select_url, snapshot, solr)
    por_no = {c["no"]: c for c in conceitos}
    consultas = {
        c["no"]: {
            "qualquer_campo": consulta_conceito(c, variante["modo_consulta"]),
            "Title": consulta_conceito_campo(c, variante["modo_consulta"], "Title"),
            "Abstract": consulta_conceito_campo(c, variante["modo_consulta"], "Abstract"),
        }
        for c in conceitos
    }
    pares = list(itertools.combinations((c["no"] for c in conceitos), 2))
    assinatura_obj = {
        "versao": 2,
        "variante_id": args.variante,
        "variante": variante,
        "anos": anos,
        "vocabulario_sha256": sha256_arquivo(termos_path),
        "fingerprint_evidencia": snapshot.get(
            "fingerprint_evidencia", snapshot["fingerprint_indice"]
        ),
        "codigo_gerador_sha256": sha256_arquivo(Path(__file__).resolve()),
        "consultas": consultas,
    }
    assinatura = sha256_json(assinatura_obj)
    checkpoint_path = saida / "checkpoint.json"
    estado = {"assinatura": assinatura, "resultados": []}
    if checkpoint_path.exists():
        estado = carregar_json(checkpoint_path)
        if estado.get("assinatura") != assinatura:
            raise SystemExit("Checkpoint pertence a outra configuração ou índice. Use outra pasta de saída.")
    resultados = estado["resultados"]
    if len(resultados) > len(pares):
        raise ValueError("Checkpoint tem mais resultados que pares")
    for i, r in enumerate(resultados):
        if (r["origem"], r["destino"]) != pares[i]:
            raise ValueError("Ordem do checkpoint não corresponde ao vocabulário")

    def consultar_par(par):
        a, b = par
        return {
            "origem": a,
            "destino": b,
            "contagens": consultar_filtros(
                select_url, filtros_par(por_no[a], por_no[b], variante), anos, solr
            ),
        }

    bloco = int(solr["bloco_checkpoint"])
    with ThreadPoolExecutor(max_workers=int(solr["workers"])) as executor:
        for inicio in range(len(resultados), len(pares), bloco):
            novos = list(executor.map(consultar_par, pares[inicio : inicio + bloco]))
            resultados.extend(novos)
            gravar_json_atomico(checkpoint_path, estado)
            print(f"{len(resultados)}/{len(pares)} pares", flush=True)

    resumos = exportar_redes(saida, resultados, por_no, anos, variante["escopo_temporal"])
    alvos = carregar_json(base / "config" / "alvos_publicados.json")
    provas = avaliar_provas_ligacao(
        saida / "relacoes_2006.csv", alvos.get("provas_ligacao_2006", [])
    )
    resumo_final = {
        "variante_id": args.variante,
        "assinatura": assinatura,
        "fingerprint_evidencia": snapshot.get(
            "fingerprint_evidencia", snapshot["fingerprint_indice"]
        ),
        "fingerprint_indice": snapshot.get(
            "fingerprint_evidencia", snapshot["fingerprint_indice"]
        ),
        "codigo_gerador_sha256": sha256_arquivo(Path(__file__).resolve()),
        "configuracao": variante,
        "redes": resumos,
        "semantica_provas_tcc": alvos.get("semantica_provas_ligacao_2006"),
        "provas_tcc": provas,
        "provas_tcc_aprovadas": all(p["aprovado"] for p in provas),
    }
    gravar_json_atomico(saida / "resumo_execucao.json", resumo_final)
    print(f"Redes gravadas em {saida}")


if __name__ == "__main__":
    main()
