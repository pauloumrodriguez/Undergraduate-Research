"""EDh (Eq. 15), rótulo DP/CP (Eq. 14) e métricas de identificação (P/R/F1/NDCG).

Funções puras, só biblioteca padrão, testáveis em CPU. As convenções seguem
config/experimento.json -> adotado.indices; nada aqui lê dados de patentes nem
fabrica Dh. Ver docs/EDH_METRICAS_V1.md.
"""
from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
import itertools
import math
from typing import Hashable, Iterable, Mapping, Optional


def rotulo_dp(c_conv: bool, c_func: bool, c_std: bool) -> str:
    """Eq. 14: DP se convergência E (função OU padrão técnico); senão CP."""
    return 'DP' if (c_conv and (c_func or c_std)) else 'CP'


def h_index(contagens: Iterable[int]) -> int:
    """Maior h inteiro tal que ao menos h valores sejam >= h."""
    ordenadas = sorted((int(c) for c in contagens), reverse=True)
    h = 0
    for posicao, valor in enumerate(ordenadas, start=1):
        if valor >= posicao:
            h = posicao
        else:
            break
    return h


def _relacao_canonica(par) -> frozenset:
    """Pares sem ordem: (a, b) e (b, a) são a mesma relação."""
    elementos = frozenset(par)
    if len(elementos) != 2:
        raise ValueError('Uma relação de convergência exige dois memes distintos.')
    return elementos


def relacoes_distintas(relacoes: Iterable) -> int:
    return len({_relacao_canonica(r) for r in relacoes})


def edh_por_tema(patentes: Iterable[Mapping], temas: Optional[Iterable[Hashable]] = None) -> dict:
    """EDh por tema numa janela.

    Cada patente: {'tema': ..., 'dp': bool, 'relacoes': [(meme_a, meme_b), ...]}, com as
    relações já filtradas pela novidade (R*). Só patentes DP contam; relações repetidas ou
    invertidas contam uma vez. Tema sem patente DP tem EDh = 0. `temas` inclui temas sem
    nenhuma patente na janela.
    """
    por_tema = defaultdict(list)
    for p in patentes:
        por_tema[p['tema']]
        if p['dp']:
            por_tema[p['tema']].append(relacoes_distintas(p.get('relacoes', ())))
    for t in (temas or ()):
        por_tema[t]
    return {t: h_index(c) for t, c in por_tema.items()}


def temas_a_partir_da_media(valores: Mapping[Hashable, float], inclusive: bool = True) -> set:
    """Temas com valor >= média aritmética exata (ou > se inclusive=False). Sem arredondar."""
    if not valores:
        return set()
    exatos = {t: Fraction(v) for t, v in valores.items()}
    media = sum(exatos.values()) / len(exatos)
    return {t for t, v in exatos.items() if (v >= media if inclusive else v > media)}


def precisao_revocacao_f1(previsto: Iterable, referencia: Iterable) -> dict:
    """Conjuntos previsto e de referência. Medida indefinida fica None, nunca 0 nem 1."""
    previsto, referencia = set(previsto), set(referencia)
    inter = len(previsto & referencia)
    p = inter / len(previsto) if previsto else None
    r = inter / len(referencia) if referencia else None
    if p is None or r is None:
        f1 = None
    else:
        f1 = 0.0 if p + r == 0 else 2 * p * r / (p + r)
    return dict(previsto=len(previsto), referencia=len(referencia), intersecao=inter,
                precisao=p, revocacao=r, f1=f1)


def ndcg(escores_previstos: Mapping[Hashable, float], relevancias: Mapping[Hashable, float]) -> Optional[float]:
    """NDCG da convenção adotada (adotado.indices.ndcg_reconstruido).

    Ordem prevista: EDh decrescente. Ganho linear = Dh do tema. Desconto 1/log2(posição+1),
    posições a partir de 1. Empates de EDh: média do ganho no bloco (média das permutações).
    IDCG: mesmos ganhos por Dh decrescente. IDCG = 0 -> None. Os dois mapas devem ter
    exatamente os mesmos temas.
    """
    if set(escores_previstos) != set(relevancias):
        raise ValueError('Escores previstos e relevâncias devem cobrir exatamente os mesmos temas.')
    if any(v < 0 for v in relevancias.values()):
        raise ValueError('Relevâncias negativas não são suportadas.')
    ordenados = sorted(escores_previstos.items(), key=lambda x: -x[1])
    ganhos = []
    for _, bloco in itertools.groupby(ordenados, key=lambda x: x[1]):
        temas = [t for t, _ in bloco]
        media = sum(relevancias[t] for t in temas) / len(temas)
        ganhos.extend([media] * len(temas))
    ideal = sorted(relevancias.values(), reverse=True)
    desconto = lambda i: 1 / math.log2(i + 2)  # i começa em 0 -> posição 1
    dcg = sum(g * desconto(i) for i, g in enumerate(ganhos))
    idcg = sum(g * desconto(i) for i, g in enumerate(ideal))
    return None if idcg == 0 else dcg / idcg


def avaliar_janela(edh: Mapping[Hashable, float], dh: Mapping[Hashable, float]) -> dict:
    """Regra escrita do artigo: EDh >= média previsto; Dh >= média referência; mais NDCG."""
    previsto = temas_a_partir_da_media(edh)
    referencia = temas_a_partir_da_media(dh)
    return dict(**precisao_revocacao_f1(previsto, referencia), ndcg=ndcg(edh, dh))
