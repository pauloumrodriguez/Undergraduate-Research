"""Gera manifestos SHA-256 e, opcionalmente, reaudita todo o corpus JSON."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipeline_common import gravar_csv_atomico, gravar_json_atomico, sha256_arquivo


ANOS = tuple(range(2006, 2016))
PASTAS_CODIGO = ("config", "docs", "notebooks", "referencias", "solr", "src", "tests")
ARQUIVOS_RAIZ = ("README.md", "STATUS_ATUAL.md", "requirements.txt", "runtime.txt", ".gitignore")


def arquivos_relevantes(projeto: Path, dados: Path):
    """Enumera somente entradas e código da replicação nova, sem artefatos legados."""
    for ano in ANOS:
        yield dados / f"{ano}_USPTO.json", "dados_brutos", True, True

    yield (
        projeto / "dados" / "vocabulario" / "termos_carbono.txt",
        "vocabulario",
        True,
        True,
    )

    for nome in ARQUIVOS_RAIZ:
        yield projeto / nome, "documentacao_ou_ambiente", False, True

    ignorados = {"__pycache__", ".ipynb_checkpoints"}
    for pasta in PASTAS_CODIGO:
        raiz = projeto / pasta
        if not raiz.exists():
            continue
        for caminho in sorted(p for p in raiz.rglob("*") if p.is_file()):
            if any(parte in ignorados for parte in caminho.parts) or caminho.suffix == ".pyc":
                continue
            yield caminho, "codigo_referencia_ou_documentacao", False, False


def auditar_corpus(dados: Path):
    totais = {}
    ids = set()
    ids_duplicados = 0
    ids_vazios = 0
    titulos_vazios_exatos = 0
    resumos_vazios_exatos = 0
    titulos_em_branco = 0
    resumos_em_branco = 0
    for ano in ANOS:
        caminho = dados / f"{ano}_USPTO.json"
        if not caminho.exists():
            raise FileNotFoundError(f"Entrada obrigatoria ausente: {caminho}")
        dados_ano = json.loads(caminho.read_text(encoding="utf-8"))
        totais[str(ano)] = len(dados_ano)
        for patente in dados_ano:
            identificador = str(patente.get("No", "")).strip()
            if not identificador:
                ids_vazios += 1
            elif identificador in ids:
                ids_duplicados += 1
            else:
                ids.add(identificador)
            titulo = str(patente.get("Title", ""))
            resumo = str(patente.get("Abstract", ""))
            titulos_vazios_exatos += titulo == ""
            resumos_vazios_exatos += resumo == ""
            titulos_em_branco += not titulo.strip()
            resumos_em_branco += not resumo.strip()
        print(f"{ano}: {len(dados_ano):,} registros auditados", flush=True)
    return {
        "total": sum(totais.values()),
        "por_ano": totais,
        "ids_unicos": len(ids),
        "ids_duplicados": ids_duplicados,
        "ids_vazios": ids_vazios,
        "titulos_vazios_exatos": titulos_vazios_exatos,
        "resumos_vazios_exatos": resumos_vazios_exatos,
        "titulos_em_branco_apos_strip": titulos_em_branco,
        "resumos_em_branco_apos_strip": resumos_em_branco,
    }


def caminho_manifesto(caminho: Path, projeto: Path) -> str:
    try:
        return str(caminho.resolve().relative_to(projeto.resolve()))
    except ValueError:
        return str(caminho.resolve())


def main():
    base = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projeto", type=Path, default=base)
    parser.add_argument("--dados", type=Path, default=base / "dados" / "brutos")
    parser.add_argument("--saida", type=Path, default=base / "evidencias")
    parser.add_argument("--auditoria-completa", action="store_true")
    args = parser.parse_args()
    projeto = args.projeto.resolve()
    dados = args.dados.resolve()
    registros = []
    for caminho, papel, imutavel, obrigatorio in arquivos_relevantes(projeto, dados):
        presente = caminho.exists()
        if presente:
            print(f"Hash: {caminho.name}", flush=True)
        registros.append(
            {
                "caminho": caminho_manifesto(caminho, projeto),
                "bytes": caminho.stat().st_size if presente else "",
                "sha256": sha256_arquivo(caminho) if presente else "",
                "papel": papel,
                "imutavel": str(imutavel).lower(),
                "obrigatorio": str(obrigatorio).lower(),
                "estado": "presente" if presente else "ausente",
            }
        )
    args.saida.mkdir(parents=True, exist_ok=True)
    gravar_csv_atomico(args.saida / "manifesto_arquivos.csv", list(registros[0]), registros)
    ausentes_obrigatorios = [
        r["caminho"]
        for r in registros
        if r["obrigatorio"] == "true" and r["estado"] == "ausente"
    ]
    resumo = {
        "projeto": str(projeto),
        "dados": str(dados),
        "arquivos_presentes": sum(r["estado"] == "presente" for r in registros),
        "arquivos_ausentes": sum(r["estado"] == "ausente" for r in registros),
        "ausentes_obrigatorios": ausentes_obrigatorios,
        "auditoria_completa": args.auditoria_completa,
    }
    if args.auditoria_completa:
        if ausentes_obrigatorios:
            raise SystemExit(
                "A auditoria completa exige todas as entradas obrigatorias. "
                f"Ausentes: {ausentes_obrigatorios}"
            )
        resumo["corpus"] = auditar_corpus(dados)
    gravar_json_atomico(args.saida / "resumo_manifesto.json", resumo)
    print(f"Manifesto: {args.saida / 'manifesto_arquivos.csv'}")


if __name__ == "__main__":
    main()
