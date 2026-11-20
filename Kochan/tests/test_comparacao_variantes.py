from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


BASE = Path(__file__).resolve().parents[1]
SRC = BASE / "src"
sys.path.insert(0, str(SRC))


def carregar_comparador():
    spec = importlib.util.spec_from_file_location(
        "comparar_variantes", SRC / "06_comparar_variantes.py"
    )
    modulo = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(modulo)
    return modulo


comparador = carregar_comparador()


class TestComparacaoVariantes(unittest.TestCase):
    def test_criterios_referem_variantes_declaradas(self):
        variantes = json.loads(
            (BASE / "config" / "variantes_rede.json").read_text(encoding="utf-8")
        )["variantes"]
        catalogo = json.loads(
            (BASE / "config" / "criterios_variantes.json").read_text(
                encoding="utf-8"
            )
        )
        criterios = catalogo["variantes"]
        derivados = set(catalogo.get("variantes_derivadas", []))
        self.assertLessEqual(set(criterios) - derivados, set(variantes))
        self.assertIn("v01_baseline_atual", criterios)
        self.assertIn("v11_apenas_termo_principal", criterios)
        self.assertIn("v12_termo_principal_mesmo_campo", criterios)

    def test_reconhece_cumulativa_derivada(self):
        self.assertEqual(
            comparador.modo_interpretado(
                "avaliacao_cumulativa.json", "cumulativo", "anual"
            ),
            "cumulativo_derivado_das_redes_anuais",
        )

    def test_reconhece_cumulativa_ja_materializada(self):
        self.assertEqual(
            comparador.modo_interpretado(
                "avaliacao_redes.json", "anual", "cumulativo_desde_2006"
            ),
            "cumulativo_ja_materializado_nos_csvs",
        )


if __name__ == "__main__":
    unittest.main()
