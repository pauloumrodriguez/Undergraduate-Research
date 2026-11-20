import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import edh_metricas as m


class RotuloDP(unittest.TestCase):
    def test_tabela_verdade(self):
        esperado = {(1, 1, 0): 'DP', (1, 0, 1): 'DP', (1, 1, 1): 'DP', (1, 0, 0): 'CP',
                    (0, 1, 1): 'CP', (0, 1, 0): 'CP', (0, 0, 1): 'CP', (0, 0, 0): 'CP'}
        for entrada, rotulo in esperado.items():
            self.assertEqual(m.rotulo_dp(*map(bool, entrada)), rotulo, entrada)


class HIndex(unittest.TestCase):
    def test_casos(self):
        for contagens, h in [([6, 5, 3, 1], 3), ([], 0), ([1], 1), ([0, 0], 0), ([4, 4, 4, 4], 4),
                             ([10], 1), ([3, 3, 3], 3), ([2, 2, 2], 2), ([5, 1, 1, 1, 1], 1)]:
            self.assertEqual(m.h_index(contagens), h, contagens)

    def test_independe_da_ordem(self):
        self.assertEqual(m.h_index([1, 6, 3, 5]), 3)


class EDh(unittest.TestCase):
    def patente(self, tema, dp, relacoes):
        return dict(tema=tema, dp=dp, relacoes=relacoes)

    def test_basico_so_conta_dp(self):
        pares = lambda n: [('a%d' % i, 'b%d' % i) for i in range(n)]
        patentes = [self.patente('T', True, pares(6)), self.patente('T', True, pares(5)),
                    self.patente('T', True, pares(3)), self.patente('T', True, pares(1)),
                    self.patente('T', False, pares(9))]  # CP ignorada
        self.assertEqual(m.edh_por_tema(patentes), {'T': 3})

    def test_tema_sem_dp_e_zero(self):
        patentes = [self.patente('T', False, [('a', 'b')])]
        self.assertEqual(m.edh_por_tema(patentes, temas=['U']), {'T': 0, 'U': 0})

    def test_relacoes_distintas_sem_ordem(self):
        patentes = [self.patente('T', True, [('a', 'b'), ('b', 'a'), ('a', 'b')])]
        self.assertEqual(m.edh_por_tema(patentes), {'T': 1})
        self.assertEqual(m.relacoes_distintas([('a', 'b'), ('b', 'a'), ('a', 'c')]), 2)

    def test_relacao_com_um_so_meme_e_rejeitada(self):
        with self.assertRaises(ValueError):
            m.relacoes_distintas([('a', 'a')])

    def test_invariante_da_ablacao_sem_c_conv(self):
        """Retirar só C_conv insere patentes com |R*| = 0, que não sustentam h >= 1."""
        base = [dict(tema='T', conv=True, func=True, std=False, relacoes=[('a', 'b'), ('c', 'd')]),
                dict(tema='T', conv=True, func=False, std=True, relacoes=[('a', 'b'), ('e', 'f')]),
                dict(tema='T', conv=False, func=True, std=False, relacoes=[]),
                dict(tema='U', conv=False, func=False, std=True, relacoes=[])]
        com = [dict(tema=p['tema'], dp=m.rotulo_dp(p['conv'], p['func'], p['std']) == 'DP',
                    relacoes=p['relacoes']) for p in base]
        sem = [dict(tema=p['tema'], dp=bool(p['func'] or p['std']), relacoes=p['relacoes']) for p in base]
        self.assertEqual(m.edh_por_tema(com, temas=['T', 'U']), m.edh_por_tema(sem, temas=['T', 'U']))


class Media(unittest.TestCase):
    def test_inclui_igualdade(self):
        self.assertEqual(m.temas_a_partir_da_media({'a': 1, 'b': 2, 'c': 3}), {'b', 'c'})
        self.assertEqual(m.temas_a_partir_da_media({'a': 1, 'b': 2, 'c': 3}, inclusive=False), {'c'})

    def test_limiar_exato_sem_arredondar(self):
        # média 4/3: 1 fica de fora, 2 entra
        self.assertEqual(m.temas_a_partir_da_media({'a': 1, 'b': 1, 'c': 2}), {'c'})
        # valor exatamente igual à média fracionária
        self.assertEqual(m.temas_a_partir_da_media({'a': 0, 'b': 1, 'c': 1, 'd': 2, 'e': 1, 'f': 1}),
                         {'b', 'c', 'd', 'e', 'f'})

    def test_todos_iguais_entram(self):
        self.assertEqual(m.temas_a_partir_da_media({'a': 5, 'b': 5}), {'a', 'b'})

    def test_vazio(self):
        self.assertEqual(m.temas_a_partir_da_media({}), set())


class PRF(unittest.TestCase):
    def test_valores(self):
        r = m.precisao_revocacao_f1({'a', 'b', 'c', 'd'}, {'a', 'b', 'e'})
        self.assertEqual((r['intersecao'], r['previsto'], r['referencia']), (2, 4, 3))
        self.assertAlmostEqual(r['precisao'], 0.5)
        self.assertAlmostEqual(r['revocacao'], 2 / 3)
        self.assertAlmostEqual(r['f1'], 2 * 0.5 * (2 / 3) / (0.5 + 2 / 3))

    def test_indefinidos_nao_viram_zero(self):
        r = m.precisao_revocacao_f1(set(), {'a'})
        self.assertIsNone(r['precisao']); self.assertIsNone(r['f1']); self.assertEqual(r['revocacao'], 0.0)
        r = m.precisao_revocacao_f1({'a'}, set())
        self.assertIsNone(r['revocacao']); self.assertIsNone(r['f1'])

    def test_sem_intersecao_f1_zero(self):
        self.assertEqual(m.precisao_revocacao_f1({'a'}, {'b'})['f1'], 0.0)


class NDCG(unittest.TestCase):
    def test_ordem_perfeita(self):
        self.assertAlmostEqual(m.ndcg({'a': 3, 'b': 2, 'c': 1}, {'a': 9, 'b': 5, 'c': 1}), 1.0)

    def test_calculo_manual_sem_empates(self):
        previstos = {'A': 3, 'B': 2, 'C': 1}
        rel = {'A': 1, 'B': 3, 'C': 2}
        dcg = 1 / math.log2(2) + 3 / math.log2(3) + 2 / math.log2(4)
        idcg = 3 / math.log2(2) + 2 / math.log2(3) + 1 / math.log2(4)
        self.assertAlmostEqual(m.ndcg(previstos, rel), dcg / idcg)

    def test_empate_usa_media_do_bloco(self):
        previstos = {'A': 2, 'B': 2, 'C': 1}
        rel = {'A': 3, 'B': 1, 'C': 2}
        dcg = 2 / math.log2(2) + 2 / math.log2(3) + 2 / math.log2(4)
        idcg = 3 / math.log2(2) + 2 / math.log2(3) + 1 / math.log2(4)
        self.assertAlmostEqual(m.ndcg(previstos, rel), dcg / idcg)
        # independe da ordem de inserção dos empatados
        self.assertAlmostEqual(m.ndcg({'B': 2, 'A': 2, 'C': 1}, rel), dcg / idcg)

    def test_todos_empatados(self):
        v = m.ndcg({'a': 1, 'b': 1, 'c': 1}, {'a': 3, 'b': 2, 'c': 1})
        media = 2
        self.assertAlmostEqual(v, (media * (1 + 1 / math.log2(3) + 1 / 2)) /
                               (3 + 2 / math.log2(3) + 1 / 2))

    def test_idcg_zero_e_indefinido(self):
        self.assertIsNone(m.ndcg({'a': 2, 'b': 1}, {'a': 0, 'b': 0}))

    def test_universos_diferentes_sao_rejeitados(self):
        with self.assertRaises(ValueError):
            m.ndcg({'a': 1, 'b': 2}, {'a': 1})

    def test_resultado_entre_zero_e_um(self):
        v = m.ndcg({'a': 1, 'b': 2, 'c': 3}, {'a': 9, 'b': 5, 'c': 1})
        self.assertTrue(0 < v < 1)


class AvaliarJanela(unittest.TestCase):
    def test_integracao(self):
        edh = {'a': 5, 'b': 5, 'c': 1, 'd': 1}
        dh = {'a': 9, 'b': 2, 'c': 8, 'd': 1}
        r = m.avaliar_janela(edh, dh)
        # EDh >= 3 -> {a,b}; Dh >= 5 -> {a,c}
        self.assertEqual((r['previsto'], r['referencia'], r['intersecao']), (2, 2, 1))
        self.assertAlmostEqual(r['f1'], 0.5)
        self.assertTrue(0 < r['ndcg'] < 1)


if __name__ == '__main__':
    unittest.main()
