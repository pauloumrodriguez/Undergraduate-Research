from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


BASE = Path(__file__).resolve().parents[1]
SRC = BASE / "src"
sys.path.insert(0, str(SRC))

from model_core import preparar_amostras  # noqa: E402
from pipeline_common import componentes, sha256_json  # noqa: E402


def carregar_script(nome, modulo):
    spec = importlib.util.spec_from_file_location(modulo, SRC / nome)
    carregado = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(carregado)
    return carregado


redes = carregar_script("03_construir_redes.py", "construir_redes")


class TestVocabulario(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((BASE / "config" / "variantes_rede.json").read_text(encoding="utf-8"))
        cls.termos = BASE / "dados" / "vocabulario" / "termos_carbono.txt"

    def test_baseline_tem_147_conceitos(self):
        conceitos, auditoria = redes.carregar_conceitos(
            self.termos, self.config["variantes"]["v01_baseline_atual"]
        )
        self.assertEqual(len(conceitos), 147)
        self.assertEqual(auditoria["pares"], 10731)

    def test_apendice_literal_tem_148_posicoes(self):
        conceitos, auditoria = redes.carregar_conceitos(
            self.termos, self.config["variantes"]["v04_148_posicoes"]
        )
        self.assertEqual(len(conceitos), 148)
        self.assertEqual(auditoria["pares"], 10878)

    def test_normalizacao_repete_limpeza_dos_documentos(self):
        self.assertEqual(
            redes.normalizar_alias("bio-based", "remover_pontuacao_ascii"),
            "biobased",
        )
        self.assertEqual(
            redes.normalizar_alias("redd+", "remover_pontuacao_ascii"),
            "redd",
        )


class TestAmostragem(unittest.TestCase):
    def test_preserva_componentes_e_classes_separadas(self):
        pesos = {
            ("a", "b"): 2,
            ("b", "c"): 1,
            ("c", "d"): 3,
            ("a", "d"): 1,
        }
        nos, observadas, positivas, negativas, ncomp = preparar_amostras(
            pesos, semente=123, fracao=0.25
        )
        self.assertEqual(ncomp, 1)
        self.assertEqual(componentes(nos, observadas), 1)
        self.assertEqual(len(positivas), 1)
        self.assertFalse(set(positivas) & set(negativas))
        self.assertEqual(observadas | set(positivas), set(pesos))


class TestConfiguracao(unittest.TestCase):
    def test_alvos_nao_sao_parametros_do_modelo(self):
        modelos = json.loads((BASE / "config" / "modelos.json").read_text(encoding="utf-8"))
        serializado = json.dumps(modelos).lower()
        self.assertNotIn("0.91", serializado)
        self.assertNotIn("roc_auc_publicado", serializado)

    def test_hash_json_independe_da_ordem(self):
        self.assertEqual(sha256_json({"a": 1, "b": 2}), sha256_json({"b": 2, "a": 1}))


if __name__ == "__main__":
    unittest.main()
