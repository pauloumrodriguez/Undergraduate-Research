"""Indexa em coleção nova ou retomável, sem apagar documentos e validando contagens."""
from __future__ import annotations

import argparse
import json
import string
import time
from pathlib import Path

from pipeline_common import carregar_json, gravar_json_atomico, sha256_arquivo


TRADUTOR = str.maketrans("", "", string.punctuation)


def requisitar(session, metodo, url, *, params=None, payload=None, tentativas=4, timeout=60):
    ultimo = None
    for tentativa in range(1, tentativas + 1):
        try:
            resposta = session.request(
                metodo, url, params=params, json=payload, timeout=timeout
            )
            resposta.raise_for_status()
            return resposta.json() if resposta.content else {}
        except Exception as erro:
            ultimo = erro
            if tentativa < tentativas:
                time.sleep(2 ** (tentativa - 1))
    raise RuntimeError(f"Falha em {metodo} {url}: {ultimo}")


def contagem(session, select_url, fq=None):
    params = {"q": "*:*", "rows": 0, "wt": "json"}
    if fq:
        params["fq"] = fq
    return int(requisitar(session, "GET", select_url, params=params)["response"]["numFound"])


def validar_schema(session, colecao_url):
    schema = requisitar(session, "GET", f"{colecao_url}/schema", params={"wt": "json"})
    campos = {c.get("name"): c for c in schema.get("schema", {}).get("fields", [])}
    faltantes = {"id", "Title", "Abstract", "Year"} - set(campos)
    if faltantes:
        raise SystemExit(f"Campos ausentes no schema: {sorted(faltantes)}")
    return schema


def main():
    import requests

    base = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz", type=Path, default=base / "dados" / "brutos")
    parser.add_argument("--base-url", default="http://localhost:8983/solr")
    parser.add_argument("--colecao", default="patents_replicacao_nova")
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--retomar", action="store_true")
    parser.add_argument("--permitir-colecao-legada", action="store_true")
    parser.add_argument("--saida", type=Path, default=base / "evidencias" / "indexacao.json")
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("batch-size deve ser positivo")
    if args.colecao == "patents" and not args.permitir_colecao_legada:
        raise SystemExit(
            "A coleção legada 'patents' foi bloqueada. Use uma coleção nova ou a opção explícita."
        )
    alvos = carregar_json(base / "config" / "alvos_publicados.json")["corpus"]
    colecao_url = f"{args.base_url.rstrip('/')}/{args.colecao}"
    select_url = f"{colecao_url}/select"
    update_docs = f"{colecao_url}/update/json/docs"
    update = f"{colecao_url}/update"
    session = requests.Session()
    schema = validar_schema(session, colecao_url)
    existente = contagem(session, select_url)
    if existente and not args.retomar:
        raise SystemExit(
            f"A coleção contém {existente} documentos. Use --retomar após conferir a coleção."
        )
    evidencia = {
        "colecao": args.colecao,
        "base_url": args.base_url,
        "batch_size": args.batch_size,
        "nenhuma_exclusao_executada": True,
        "schema": schema,
        "anos": {},
    }
    for ano in range(2006, 2016):
        esperado = int(alvos["por_ano"][str(ano)])
        antes = contagem(session, select_url, f"Year:{ano}")
        caminho = args.raiz.resolve() / f"{ano}_USPTO.json"
        if antes == esperado:
            evidencia["anos"][str(ano)] = {
                "estado": "já_completo",
                "contagem": antes,
                "arquivo_sha256": sha256_arquivo(caminho),
            }
            gravar_json_atomico(args.saida, evidencia)
            continue
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        if len(dados) != esperado:
            raise RuntimeError(f"{ano}: arquivo tem {len(dados)}, esperado {esperado}")
        for inicio in range(0, len(dados), args.batch_size):
            lote = []
            for patente in dados[inicio : inicio + args.batch_size]:
                lote.append(
                    {
                        "id": patente["No"],
                        "Title": str(patente.get("Title", "")).translate(TRADUTOR),
                        "Abstract": str(patente.get("Abstract", "")).translate(TRADUTOR),
                        "Year": ano,
                    }
                )
            requisitar(
                session,
                "POST",
                update_docs,
                params={"overwrite": "true", "wt": "json"},
                payload=lote,
            )
            if (inicio // args.batch_size) % 25 == 0:
                print(f"{ano}: {min(inicio + len(lote), len(dados))}/{len(dados)}", flush=True)
        requisitar(session, "POST", update, params={"wt": "json"}, payload={"commit": {}})
        depois = contagem(session, select_url, f"Year:{ano}")
        if depois != esperado:
            raise RuntimeError(f"{ano}: Solr retornou {depois}, esperado {esperado}")
        evidencia["anos"][str(ano)] = {
            "estado": "indexado_e_validado",
            "contagem_antes": antes,
            "contagem_depois": depois,
            "arquivo_sha256": sha256_arquivo(caminho),
        }
        gravar_json_atomico(args.saida, evidencia)
    total = contagem(session, select_url)
    evidencia["total_final"] = total
    evidencia["aprovado"] = total == int(alvos["total"])
    gravar_json_atomico(args.saida, evidencia)
    if not evidencia["aprovado"]:
        raise SystemExit(f"Total final {total}; esperado {alvos['total']}")
    print(f"Indexação validada: {total:,} documentos")


if __name__ == "__main__":
    main()
