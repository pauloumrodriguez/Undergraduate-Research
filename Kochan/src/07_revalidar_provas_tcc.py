"""Corrige e revalida as provas binárias da Tabela 3 nos resultados existentes."""
from __future__ import annotations

import argparse
from pathlib import Path

from pipeline_common import carregar_json, gravar_json_atomico


def carregar_gerador(base: Path):
    import importlib.util

    caminho = base / "src" / "03_construir_redes.py"
    spec = importlib.util.spec_from_file_location("construir_redes", caminho)
    modulo = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(modulo)
    return modulo


def main() -> None:
    base = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=base / "runs" / "redes")
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    alvos = carregar_json(base / "config" / "alvos_publicados.json")
    provas = alvos["provas_ligacao_2006"]
    gerador = carregar_gerador(base)
    alterados = 0
    for pasta in sorted(p for p in args.runs.iterdir() if p.is_dir()):
        resumo_path = pasta / "resumo_execucao.json"
        rede_path = pasta / "relacoes_2006.csv"
        if not resumo_path.exists() or not rede_path.exists():
            continue
        resumo = carregar_json(resumo_path)
        anteriores = resumo.get("provas_tcc", [])
        if anteriores and "ligacao_observada" not in anteriores[0]:
            resumo.setdefault(
                "provas_tcc_interpretacao_anterior_incorreta", anteriores
            )
        corrigidas = gerador.avaliar_provas_ligacao(rede_path, provas)
        resumo["semantica_provas_tcc"] = alvos[
            "semantica_provas_ligacao_2006"
        ]
        resumo["provas_tcc"] = corrigidas
        resumo["provas_tcc_aprovadas"] = all(p["aprovado"] for p in corrigidas)
        falhas = sum(not p["aprovado"] for p in corrigidas)
        print(f"{pasta.name}: {len(corrigidas) - falhas}/{len(corrigidas)} provas")
        if args.aplicar:
            gravar_json_atomico(resumo_path, resumo)
            alterados += 1
    if args.aplicar:
        print(f"Resumos atualizados: {alterados}")
    else:
        print("Simulação concluída; use --aplicar para gravar.")


if __name__ == "__main__":
    main()
