"""Captura o estado do Solr e valida total, anos, schema e documentos-amostra."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import time
from pathlib import Path

from pipeline_common import (
    carregar_json,
    gravar_json_atomico,
    gravar_texto_atomico,
    sha256_json,
)


def obter_json(session, url, *, params=None, tentativas=3, timeout=30):
    ultimo = None
    for tentativa in range(1, tentativas + 1):
        try:
            resposta = session.get(url, params=params, timeout=timeout)
            resposta.raise_for_status()
            return resposta.json()
        except Exception as erro:  # mensagem preservada no erro final
            ultimo = erro
            if tentativa < tentativas:
                time.sleep(2 ** (tentativa - 1))
    raise RuntimeError(f"Falha após {tentativas} tentativas em {url}: {ultimo}")


def obter_texto(session, url, *, params=None, tentativas=3, timeout=30):
    ultimo = None
    for tentativa in range(1, tentativas + 1):
        try:
            resposta = session.get(url, params=params, timeout=timeout)
            resposta.raise_for_status()
            return resposta.content.decode("utf-8")
        except Exception as erro:
            ultimo = erro
            if tentativa < tentativas:
                time.sleep(2 ** (tentativa - 1))
    raise RuntimeError(f"Falha após {tentativas} tentativas em {url}: {ultimo}")


def sem_metadados_volateis(valor):
    """Remove tempos de resposta que mudam sem alterar schema/configuração."""
    if isinstance(valor, dict):
        return {
            chave: sem_metadados_volateis(conteudo)
            for chave, conteudo in valor.items()
            if chave != "responseHeader"
        }
    if isinstance(valor, list):
        return [sem_metadados_volateis(item) for item in valor]
    return valor


def consulta_contagem(session, select_url, fq=None):
    params = {"q": "*:*", "rows": 0, "wt": "json"}
    if fq:
        params["fq"] = fq
    dados = obter_json(session, select_url, params=params)
    return int(dados["response"]["numFound"])


def main():
    import requests

    base = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz", type=Path, default=base)
    parser.add_argument("--base-url", default="http://localhost:8983/solr")
    parser.add_argument("--colecao", default="patents_replicacao_nova")
    parser.add_argument(
        "--saida", type=Path, default=base / "evidencias" / "solr_snapshot_v2.json"
    )
    parser.add_argument(
        "--exportar-configset", type=Path, default=base / "solr" / "configset_export"
    )
    args = parser.parse_args()
    alvos = carregar_json(base / "config" / "alvos_publicados.json")["corpus"]
    colecao_url = f"{args.base_url.rstrip('/')}/{args.colecao}"
    select_url = f"{colecao_url}/select"
    session = requests.Session()

    total = consulta_contagem(session, select_url)
    por_ano = {
        str(ano): consulta_contagem(session, select_url, f"Year:{ano}")
        for ano in range(2006, 2016)
    }
    schema = obter_json(session, f"{colecao_url}/schema", params={"wt": "json"})
    config = obter_json(session, f"{colecao_url}/config", params={"wt": "json"})
    recursos_configset = {}
    for nome in ("stopwords.txt", "synonyms.txt"):
        conteudo = obter_texto(session, f"{colecao_url}/admin/file", params={"file": nome})
        recursos_configset[nome] = {
            "sha256": hashlib.sha256(conteudo.encode("utf-8")).hexdigest(),
            "conteudo": conteudo,
        }
        gravar_texto_atomico(args.exportar_configset / nome, conteudo)
    try:
        sistema = obter_json(
            session, f"{args.base_url.rstrip('/')}/admin/info/system", params={"wt": "json"}
        )
    except Exception as erro:
        sistema = {"erro": str(erro)}

    amostras = {}
    for ano in (2006, 2010, 2015):
        amostras[str(ano)] = obter_json(
            session,
            select_url,
            params={
                "q": "*:*",
                "fq": f"Year:{ano}",
                "rows": 3,
                "fl": "id,Title,Abstract,Year",
                "sort": "id asc",
                "wt": "json",
            },
        )["response"]["docs"]

    validacoes = {
        "total_exato": total == int(alvos["total"]),
        "anos_exatos": por_ano == {k: int(v) for k, v in alvos["por_ano"].items()},
        "campos_necessarios": all(
            any(campo.get("name") == nome for campo in schema.get("schema", {}).get("fields", []))
            for nome in ("Title", "Abstract", "Year")
        ),
        "recursos_configset_capturados": all(
            recursos_configset[nome]["conteudo"] is not None
            for nome in ("stopwords.txt", "synonyms.txt")
        ),
    }
    conteudo_estavel = {
        "colecao": args.colecao,
        "total": total,
        "por_ano": por_ano,
        "schema": sem_metadados_volateis(schema),
        "config": sem_metadados_volateis(config),
        "recursos_configset": recursos_configset,
        "amostras": amostras,
        "validacoes": validacoes,
    }
    fingerprint = sha256_json(conteudo_estavel)
    snapshot = {
        **conteudo_estavel,
        "base_url": args.base_url,
        "capturado_em_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sistema": sistema,
        "fingerprint_evidencia": fingerprint,
        "fingerprint_indice": fingerprint,
        "aviso_fingerprint": (
            "Identifica contagens, schema/config efetivos, recursos relevantes e nove "
            "documentos-amostra; não é um hash criptográfico de todos os 2.000.147 documentos."
        ),
        "aprovado": all(validacoes.values()),
    }
    gravar_json_atomico(args.saida, snapshot)
    print(f"Total: {total:,}; anos exatos: {validacoes['anos_exatos']}")
    print(f"Fingerprint da evidência: {snapshot['fingerprint_evidencia']}")
    print(f"Configset relevante: {args.exportar_configset}")
    print(f"Snapshot: {args.saida}")
    if not snapshot["aprovado"]:
        raise SystemExit("O índice Solr não passou pelas validações obrigatórias.")


if __name__ == "__main__":
    main()
