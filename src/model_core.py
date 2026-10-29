"""Núcleo único de amostragem e passeios usado pelos experimentos novos."""
from __future__ import annotations

import math
import random
from itertools import combinations

from pipeline_common import componentes


def preparar_amostras(
    arestas_com_peso: dict[tuple[str, str], int],
    semente: int,
    fracao: float,
    negativos: str = "todos",
    negative_ratio: float | None = None,
):
    if not 0 < fracao < 1:
        raise ValueError("A fração de arestas removidas deve estar entre zero e um")
    original = set(arestas_com_peso)
    nos = sorted({n for par in original for n in par})
    n_componentes = componentes(nos, original)
    observadas = set(original)
    candidatas = sorted(original)
    rng = random.Random(semente)
    rng.shuffle(candidatas)
    alvo = math.floor(len(original) * fracao)
    positivas = []
    for par in candidatas:
        if len(positivas) == alvo:
            break
        observadas.remove(par)
        if componentes(nos, observadas) == n_componentes:
            positivas.append(par)
        else:
            observadas.add(par)
    if len(positivas) != alvo:
        raise RuntimeError(f"Só foi possível ocultar {len(positivas)} de {alvo} arestas")
    universo_negativo = sorted(set(combinations(nos, 2)) - original)
    if negativos == "todos":
        negativas = universo_negativo
    elif negativos == "razao":
        if negative_ratio is None or negative_ratio <= 0:
            raise ValueError("negative_ratio deve ser positivo quando negativos='razao'")
        quantidade = min(len(universo_negativo), math.ceil(len(positivas) * negative_ratio))
        negativas = sorted(rng.sample(universo_negativo, quantidade))
    else:
        raise ValueError(f"Estratégia de negativos desconhecida: {negativos}")
    if set(positivas) & (observadas | set(negativas)):
        raise AssertionError("Vazamento entre positivas, negativas e grafo observado")
    if observadas | set(positivas) != original:
        raise AssertionError("A restauração das arestas originais falhou")
    if componentes(nos, observadas) != n_componentes:
        raise AssertionError("A remoção alterou o número de componentes")
    return nos, observadas, sorted(positivas), negativas, n_componentes


def gerar_passeios(
    nos,
    observadas,
    pesos_originais,
    semente,
    quantidade,
    tamanho,
    p,
    q,
    weighted=False,
):
    if p <= 0 or q <= 0:
        raise ValueError("p e q devem ser positivos")
    adj = {n: set() for n in nos}
    for a, b in observadas:
        adj[a].add(b)
        adj[b].add(a)
    rng = random.Random(semente)
    resultado = []
    for _ in range(int(quantidade)):
        ordem = sorted(nos)
        rng.shuffle(ordem)
        for inicio in ordem:
            caminho = [inicio]
            while len(caminho) < int(tamanho):
                atual = caminho[-1]
                vizinhos = sorted(adj[atual])
                if not vizinhos:
                    break
                if len(caminho) == 1:
                    if weighted:
                        ws = [math.log1p(pesos_originais[tuple(sorted((atual, x)))]) for x in vizinhos]
                        proximo = rng.choices(vizinhos, weights=ws, k=1)[0]
                    else:
                        proximo = rng.choice(vizinhos)
                else:
                    anterior = caminho[-2]
                    ws = []
                    for candidato in vizinhos:
                        alpha = 1 / p if candidato == anterior else 1 if candidato in adj[anterior] else 1 / q
                        peso_aresta = (
                            math.log1p(pesos_originais[tuple(sorted((atual, candidato)))])
                            if weighted
                            else 1.0
                        )
                        ws.append(alpha * peso_aresta)
                    proximo = rng.choices(vizinhos, weights=ws, k=1)[0]
                caminho.append(proximo)
            resultado.append(caminho)
    return resultado


def sementes(ano: int, repeticao: int, base: int):
    raiz = int(base) + repeticao * 1000 + (ano - 2006) * 10
    return {
        "amostras": raiz + 1,
        "passeios": raiz + 2,
        "word2vec": raiz + 3,
        "divisao": raiz + 4,
        "regressao": raiz + 5,
    }
