"""Valida a estrutura da replicação independente antes da entrega ou reexecução."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipeline_common import gravar_json_atomico


ANOS = tuple(range(2006, 2016))


def main() -> None:
    base = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--permitir-dados-ausentes", action="store_true")
    parser.add_argument(
        "--saida", type=Path, default=base / "evidencias" / "validacao_pacote.json"
    )
    args = parser.parse_args()

    obrigatorios = [
        base / "README.md",
        base / "STATUS_ATUAL.md",
        base / "requirements.txt",
        base / "dados" / "vocabulario" / "termos_carbono.txt",
        base / "config" / "alvos_publicados.json",
        base / "config" / "variantes_rede.json",
        base / "docs" / "GUIA_EXECUCAO_COMPLETA.md",
        base / "referencias" / "Kochan_TCC_2022.pdf",
        base / "referencias" / "Kochan_artigo_2024.pdf",
        base / "solr" / "configset_replicacao" / "conf" / "managed-schema.xml",
    ]
    dados = [base / "dados" / "brutos" / f"{ano}_USPTO.json" for ano in ANOS]
    ausentes = [str(p.relative_to(base)) for p in obrigatorios if not p.exists()]
    dados_ausentes = [str(p.relative_to(base)) for p in dados if not p.exists()]

    json_invalidos = []
    for caminho in sorted(base.rglob("*.json")):
        try:
            json.loads(caminho.read_text(encoding="utf-8"))
        except Exception as erro:
            json_invalidos.append(
                {"caminho": str(caminho.relative_to(base)), "erro": str(erro)}
            )

    notebooks_invalidos = []
    for caminho in sorted((base / "notebooks").glob("*.ipynb")):
        try:
            conteudo = json.loads(caminho.read_text(encoding="utf-8"))
            if conteudo.get("nbformat") != 4 or not isinstance(conteudo.get("cells"), list):
                raise ValueError("estrutura de notebook inesperada")
        except Exception as erro:
            notebooks_invalidos.append(
                {"caminho": str(caminho.relative_to(base)), "erro": str(erro)}
            )

    aprovado = not ausentes and not json_invalidos and not notebooks_invalidos
    if dados_ausentes and not args.permitir_dados_ausentes:
        aprovado = False
    relatorio = {
        "aprovado": aprovado,
        "arquivos_obrigatorios_ausentes": ausentes,
        "dados_brutos_ausentes": dados_ausentes,
        "dados_ausentes_permitidos": args.permitir_dados_ausentes,
        "json_invalidos": json_invalidos,
        "notebooks_invalidos": notebooks_invalidos,
        "notebooks_encontrados": len(list((base / "notebooks").glob("*.ipynb"))),
        "variantes_entregues": len(list((base / "runs" / "redes").glob("v*"))),
    }
    gravar_json_atomico(args.saida, relatorio)
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))
    if not aprovado:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
