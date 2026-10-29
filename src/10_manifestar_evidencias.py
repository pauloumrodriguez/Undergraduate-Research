"""Gera hashes de todas as evidências, resultados e recursos Solr preservados."""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from pipeline_common import (
    gravar_csv_atomico,
    gravar_json_atomico,
    sha256_arquivo,
)


def main() -> None:
    base = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--saida",
        type=Path,
        default=base / "evidencias" / "manifesto_evidencias.csv",
    )
    args = parser.parse_args()
    ignorados = {
        args.saida.resolve(),
        args.saida.with_suffix(".json").resolve(),
    }
    arquivos = []
    for raiz in (
        base / "evidencias",
        base / "runs",
        base / "solr" / "configset_export",
    ):
        if not raiz.exists():
            continue
        for caminho in sorted(p for p in raiz.rglob("*") if p.is_file()):
            if caminho.resolve() in ignorados or "__pycache__" in caminho.parts:
                continue
            arquivos.append(caminho)
    registros = []
    for caminho in arquivos:
        print(f"Hash: {caminho.relative_to(base)}", flush=True)
        registros.append(
            {
                "caminho": str(caminho.relative_to(base)),
                "bytes": caminho.stat().st_size,
                "sha256": sha256_arquivo(caminho),
            }
        )
    gravar_csv_atomico(args.saida, list(registros[0]), registros)
    gravar_json_atomico(
        args.saida.with_suffix(".json"),
        {
            "gerado_em_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "arquivos": len(registros),
            "bytes": sum(r["bytes"] for r in registros),
            "escopo": ["evidencias", "runs", "solr/configset_export"],
            "manifesto_csv": args.saida.resolve().relative_to(base.resolve()).as_posix(),
        },
    )
    print(f"Arquivos manifestados: {len(registros)}")


if __name__ == "__main__":
    main()
