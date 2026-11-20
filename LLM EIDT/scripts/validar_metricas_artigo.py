"""Recalcula P/R/F1/NDCG a partir das Tabelas 6-8 do artigo e compara com a Tabela 9.

Só usa as tabelas transcritas em dados/referencia/tabelas_6_8_artigo_transcritas.json e
scripts/edh_metricas.py. A convenção de NDCG é a adotada antes desta verificação; as
convenções alternativas aparecem apenas como sensibilidade e não são adotadas.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edh_metricas as m

FONTE = 'dados/referencia/tabelas_6_8_artigo_transcritas.json'
SAIDA = 'resultados/etapa_6/validacao_metricas_artigo_v1'


def norm(nome: str) -> str:
    return re.sub(r'\s+', ' ', nome.lower().replace('&', ' and ')).strip()


def linhas(rows):
    return [(norm(x['tema']), x['valor']) for x in rows]


def mapa_primeira_ocorrencia(rows):
    d = {}
    for t, v in linhas(rows):
        d.setdefault(t, v)
    return d


def arred(x):
    return None if x is None else round(x, 4)


def comparar(calc, pub):
    return {k: dict(calculado=arred(calc[k]), publicado=pub[k],
                    confere=calc[k] is not None and abs(round(calc[k], 4) - pub[k]) < 1e-9)
            for k in ('precisao', 'revocacao', 'f1')}


def ndcg_sensibilidade(edh_linhas, rel, ganho, empate):
    """Convenções alternativas, só para sensibilidade (não adotadas)."""
    g = (lambda v: v) if ganho == 'linear' else (lambda v: 2 ** v - 1)
    ordenados = []
    for _, bloco in itertools.groupby(edh_linhas, key=lambda x: x[1]):
        vals = [g(rel[t]) for t, _ in bloco]
        ordenados += [sum(vals) / len(vals)] * len(vals) if empate == 'media' else vals
    ideal = sorted((g(v) for v in rel.values()), reverse=True)
    d = lambda i: 1 / math.log2(i + 2)
    return sum(x * d(i) for i, x in enumerate(ordenados)) / sum(x * d(i) for i, x in enumerate(ideal))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--raiz', type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    raiz = args.raiz.resolve()
    fonte = raiz / FONTE
    dados = json.loads(fonte.read_bytes())
    saida = dict(estado='validacao_metricas_artigo', data=datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                 fonte=FONTE, sha256_fonte=hashlib.sha256(fonte.read_bytes()).hexdigest(),
                 convencao_ndcg='linear, desempate pela média do bloco, 1/log2(posição+1), temas únicos (adotado.indices.ndcg_reconstruido)',
                 janelas={})
    for janela, v in dados['janelas'].items():
        edh_l = linhas(v['ranking_edh']); dh_l = linhas(v['ranking_dh'])
        edh = dict(edh_l); dh = mapa_primeira_ocorrencia(v['ranking_dh'])
        pub = v['tabela9']
        info = dict(tabela=v['tabela'], temas_edh=len(edh), temas_dh_unicos=len(dh),
                    media_edh=sum(edh.values()) / len(edh),
                    media_dh_impressa=sum(x for _, x in dh_l) / len(dh_l))
        if len(dh) == len(edh):
            r = m.avaliar_janela(edh, dh)
            info['regra_escrita'] = dict(conjuntos=dict(edh=r['previsto'], dh=r['referencia'], intersecao=r['intersecao']),
                                         metricas=comparar(r, pub),
                                         ndcg=dict(calculado=arred(r['ndcg']), publicado=pub['ndcg'],
                                                   confere=abs(round(r['ndcg'], 4) - pub['ndcg']) < 1e-9))
            sens = {}
            for ganho in ('linear', 'exponencial_2^rel-1'):
                for empate in ('media', 'ordem_impressa'):
                    sens[f'{ganho}|{empate}'] = arred(ndcg_sensibilidade(edh_l, dh, 'linear' if ganho == 'linear' else 'exp',
                                                                       'media' if empate == 'media' else 'impressa'))
            info['sensibilidade_ndcg_nao_adotada'] = sens
        else:
            # Tabela 7: Dh repete dois temas e omite Gene therapy e Biomaterials & delivery.
            ausentes = sorted(set(edh) - set(dh))
            info['ressalva'] = dict(
                dh_repete=sorted({t for t, _ in dh_l if sum(1 for u, _ in dh_l if u == t) > 1}),
                dh_omite=ausentes)
            # regra escrita sobre os temas únicos da coluna Dh (a repetição fica abaixo do corte nas duas leituras)
            r = m.precisao_revocacao_f1(m.temas_a_partir_da_media(edh), m.temas_a_partir_da_media(dh))
            info['regra_escrita'] = dict(conjuntos=dict(edh=r['previsto'], dh=r['referencia'], intersecao=r['intersecao']),
                                         metricas=comparar(r, pub))
            # corte gráfico: linha horizontal acima da 8a posição de EDh e da 10a de Dh
            cg_edh = {t for t, _ in edh_l[:8]}; cg_dh = {t for t, _ in dh_l[:10]}
            g = m.precisao_revocacao_f1(cg_edh, cg_dh)
            info['corte_grafico_inferido'] = dict(
                regra='8 primeiros do ranking EDh e 10 primeiros do ranking Dh (inferido dos números da Tabela 9 e de config/experimento.json)',
                conjuntos=dict(edh=g['previsto'], dh=g['referencia'], intersecao=g['intersecao']),
                metricas=comparar(g, pub))
            hip = {}
            for nome, extra in (('H1_linhas15_16=GeneTherapy8,Biomaterials7', {'gene therapy': 8, 'biomaterials and delivery': 7}),
                                ('H2_linhas15_16=GeneTherapy7,Biomaterials8', {'gene therapy': 7, 'biomaterials and delivery': 8})):
                rel = {**dh, **extra}
                hip[nome] = dict(ndcg=arred(m.ndcg(edh, rel)), publicado=pub['ndcg'])
            rel14 = {t: dh[t] for t in dh}
            hip['H0_somente_14_temas_com_Dh'] = dict(ndcg=arred(m.ndcg({t: edh[t] for t in rel14}, rel14)), publicado=pub['ndcg'])
            info['ndcg_hipoteses_identidade'] = hip
        saida['janelas'][janela] = info
    # média das três janelas com os valores publicados da Tabela 9 e com os recalculados
    pubs = [v['tabela9'] for v in dados['janelas'].values()]
    media = lambda k: sum(p[k] for p in pubs) / 3
    saida['media_tabela9_recalculada_dos_valores_publicados'] = {k: round(media(k), 4) for k in ('precisao', 'revocacao', 'f1', 'ndcg')}
    saida['media_tabela9_publicada'] = dados['media_tabela9']
    destino = raiz / SAIDA
    destino.mkdir(parents=True, exist_ok=True)
    (destino / 'validacao.json').write_text(json.dumps(saida, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(saida, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
