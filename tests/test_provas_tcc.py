from __future__ import annotations

import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


BASE = Path(__file__).resolve().parents[1]
SRC = BASE / "src"
sys.path.insert(0, str(SRC))


def carregar_gerador():
    spec = importlib.util.spec_from_file_location(
        "construir_redes_provas", SRC / "03_construir_redes.py"
    )
    modulo = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(modulo)
    return modulo


gerador = carregar_gerador()


class TestProvasTcc(unittest.TestCase):
    def test_ligacao_e_binaria_nao_contagem_de_documentos(self):
        with tempfile.TemporaryDirectory(dir=BASE) as pasta:
            rede = Path(pasta) / "relacoes_2006.csv"
            with rede.open("w", encoding="utf-8", newline="") as arquivo:
                writer = csv.DictWriter(
                    arquivo,
                    fieldnames=[
                        "origem_rotulo",
                        "destino_rotulo",
                        "coocorrencias",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "origem_rotulo": "recycling",
                        "destino_rotulo": "biogas",
                        "coocorrencias": 2,
                    }
                )
            provas = gerador.avaliar_provas_ligacao(
                rede,
                [
                    {
                        "termo_a": "recycling",
                        "termo_b": "biogas",
                        "ligacao_esperada": 1,
                    },
                    {
                        "termo_a": "carbon black",
                        "termo_b": "bioprocessing",
                        "ligacao_esperada": 0,
                    },
                ],
            )
        self.assertTrue(provas[0]["aprovado"])
        self.assertEqual(provas[0]["ligacao_observada"], 1)
        self.assertEqual(provas[0]["pesos_registros_encontrados"], [2])
        self.assertTrue(provas[1]["aprovado"])
        self.assertEqual(provas[1]["ligacao_observada"], 0)


if __name__ == "__main__":
    unittest.main()
