"""Utilidades compartilhadas pela camada de replicação melhorada."""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Iterable


def sha256_arquivo(caminho: Path, bloco: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        while pedaco := arquivo.read(bloco):
            digest.update(pedaco)
    return digest.hexdigest()


def sha256_json(valor) -> str:
    serializado = json.dumps(
        valor, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(serializado).hexdigest()


def gravar_texto_atomico(caminho: Path, texto: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    with temporario.open("w", encoding="utf-8", newline="") as arquivo:
        arquivo.write(texto)
        arquivo.flush()
        os.fsync(arquivo.fileno())
    os.replace(temporario, caminho)


def gravar_json_atomico(caminho: Path, valor) -> None:
    gravar_texto_atomico(
        caminho, json.dumps(valor, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )


def gravar_csv_atomico(caminho: Path, colunas: list[str], registros: Iterable[dict]) -> None:
    import io

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=colunas)
    writer.writeheader()
    writer.writerows(registros)
    gravar_texto_atomico(caminho, buffer.getvalue())


def carregar_json(caminho: Path):
    return json.loads(caminho.read_text(encoding="utf-8"))


def carregar_rede(caminho: Path) -> dict[tuple[str, str], int]:
    arestas: dict[tuple[str, str], int] = {}
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            a = (linha.get("origem") or linha.get("origem_id") or "").strip()
            b = (linha.get("destino") or linha.get("destino_id") or "").strip()
            peso = int(linha["coocorrencias"])
            par = tuple(sorted((a, b)))
            if not a or not b or a == b or peso <= 0 or par in arestas:
                raise ValueError(f"Aresta inválida ou duplicada em {caminho}: {par}")
            arestas[par] = peso
    return arestas


def estatisticas_rede(arestas: dict[tuple[str, str], int]) -> dict[str, int]:
    nos = {no for par in arestas for no in par}
    return {
        "nos": len(nos),
        "arestas": len(arestas),
        "peso_total": sum(arestas.values()),
    }


def componentes(nos: Iterable[str], arestas: Iterable[tuple[str, str]]) -> int:
    nos = set(nos)
    adj = {no: set() for no in nos}
    for a, b in arestas:
        adj[a].add(b)
        adj[b].add(a)
    restantes = set(nos)
    total = 0
    while restantes:
        total += 1
        pilha = [restantes.pop()]
        while pilha:
            novos = adj[pilha.pop()] & restantes
            restantes.difference_update(novos)
            pilha.extend(novos)
    return total
