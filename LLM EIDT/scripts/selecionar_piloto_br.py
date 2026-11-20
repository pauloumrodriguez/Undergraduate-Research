"""Select the frozen Brazilian PATSTAT pilot using only the Python standard library.

The unit is a DOCDB family, not a publication. The earlier split is preserved.
The source query used IPC A61/C12N/C12Q; this pilot further requires an observed
family CPC starting with A61 or C12N because IPC was not retained in the package.
"""

from __future__ import annotations

import argparse
import ast
import csv
from collections import Counter
from datetime import date
import hashlib
import io
import json
from pathlib import Path
import re
import tempfile
import zipfile


PARTITIONS = {"treino": "train", "validacao": "validation", "teste": "test"}
EXPECTED_SOURCE = {"treino": 800, "validacao": 100, "teste": 100}
PREFIXES = ("A61", "C12N")
RAW_FIELDS = {
    "patent_id", "appln_id", "appln_auth", "appln_nr", "application_date",
    "application_year", "title", "title_language", "abstract",
    "abstract_language", "cpc_codes", "cpc_primary",
}
OUTPUT_FIELDS = [
    "id_familia_docdb", "appln_id", "appln_auth", "appln_nr",
    "data_deposito", "ano_deposito", "titulo", "idioma_titulo", "resumo",
    "idioma_resumo", "cpc_codes", "cpc_proxy", "janela", "particao",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_source(archive: bytes) -> tuple[list[dict], dict[str, str], dict]:
    """Verify the CSV, family labels and the three original disjoint splits."""
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        names = zf.namelist()
        require(len(names) == len(set(names)), "ZIP com nomes de arquivo duplicados.")
        required = {"manifest.json", "patents_lora_1000_preview.csv"}
        required.update(f"lora_{part}.jsonl" for part in PARTITIONS.values())
        require(required.issubset(names), "ZIP incompleto: faltam manifest/CSV/partições.")
        # Do not extract arbitrary member paths from the archive.
        manifest = json.loads(zf.read("manifest.json").decode("utf-8-sig"))
        require(manifest.get("total") == 1000, "O manifesto deve declarar 1.000 famílias.")
        require(manifest.get("start_year") == 2010 and manifest.get("end_year") == 2024,
                "Período inesperado no manifesto original.")
        reader = csv.DictReader(io.StringIO(
            zf.read("patents_lora_1000_preview.csv").decode("utf-8-sig"), newline=""))
        require(set(reader.fieldnames or []) == RAW_FIELDS, "Schema inesperado no CSV original.")
        rows = list(reader)
        require(len(rows) == 1000, "O CSV completo deve conter 1.000 famílias.")
        by_id = {}
        for row in rows:
            require(None not in row and all(v is not None for v in row.values()),
                    "Linha CSV malformada.")
            family = row["patent_id"]
            require(bool(re.fullmatch(r"[1-9][0-9]*", family)), "DOCDB family ID inválido.")
            require(family not in by_id, f"Família duplicada no CSV: {family}.")
            require(bool(re.fullmatch(r"[1-9][0-9]*", row["appln_id"])),
                    f"appln_id inválido: {family}.")
            for field in ("title", "abstract", "appln_auth", "appln_nr", "cpc_primary"):
                require(bool(row[field].strip()), f"{field} ausente: família {family}.")
            filed = date.fromisoformat(row["application_date"])
            year = int(row["application_year"])
            require(filed.year == year and 2010 <= year <= 2024,
                    f"Ano/data de depósito inconsistente: família {family}.")
            for field in ("title_language", "abstract_language"):
                require(row[field] in {"pt", "en"},
                        f"Idioma fora do perfil pt/en em {field}: família {family}.")
            codes = ast.literal_eval(row["cpc_codes"])
            require(isinstance(codes, list) and len(codes) > 0
                    and all(isinstance(code, str) and bool(code.strip()) for code in codes),
                    f"Lista CPC inválida: família {family}.")
            require(len(codes) == len(set(codes)), f"CPC duplicado: família {family}.")
            require(row["cpc_primary"] == sorted(codes)[0],
                    f"CPC proxy diverge da regra alfabética original: família {family}.")
            row["_codes"] = codes
            row["_year"] = year
            by_id[family] = row

        membership = {}
        for part, original_name in PARTITIONS.items():
            records = [json.loads(line) for line in
                       zf.read(f"lora_{original_name}.jsonl").decode("utf-8-sig").splitlines()
                       if line.strip()]
            expected = EXPECTED_SOURCE[part]
            require(len(records) == expected and manifest.get(original_name) == expected,
                    f"Partição original {original_name} deveria ter {expected} registros.")
            for record in records:
                family = str(record.get("patent_id", ""))
                require(family in by_id, f"Família de JSONL ausente do CSV: {family}.")
                require(family not in membership,
                        f"Família repetida ou sobreposta nas partições originais: {family}.")
                require(record.get("output") == by_id[family]["cpc_primary"],
                        f"Rótulo do JSONL não corresponde ao CSV: família {family}.")
                membership[family] = part
        require(set(membership) == set(by_id), "IDs do CSV e das partições divergem.")
    return rows, membership, manifest


def language_counts(rows: list[dict]) -> dict:
    return dict(sorted(Counter(
        f"{r['title_language']}/{r['abstract_language']}" for r in rows).items()))


def has_scope(code: str) -> bool:
    return re.sub(r"\s+", "", code).upper().startswith(PREFIXES)


def build_outputs(archive: bytes, config: dict) -> tuple[bytes, bytes, dict]:
    """Return deterministic CSV/audit bytes without writing or training a model."""
    pilot = config["piloto"]
    sampling = pilot["amostragem"]
    configured_prefixes = pilot["coleta"].get("prefixos_cpc_piloto")
    require(isinstance(configured_prefixes, list) and len(configured_prefixes) == len(PREFIXES)
            and set(configured_prefixes) == set(PREFIXES),
            "O perfil brasileiro v1 exige prefixos_cpc_piloto A61 e C12N.")
    source_hash = sha256(archive)
    require(pilot["coleta"].get("sha256_zip") == source_hash,
            "SHA-256 do ZIP diverge do pacote congelado em experimento.json.")
    seed = sampling["semente"]
    require(isinstance(seed, int) and not isinstance(seed, bool), "Semente deve ser inteira.")
    require(sampling["total"] == 200, "Este perfil requer exatamente 200 famílias.")
    expected_partitions = {"treino": 160, "validacao": 20, "teste": 20}
    require(sampling["particoes"] == expected_partitions, "Quotas esperadas: 160/20/20.")
    windows = sampling["janelas"]
    require([(w["inicio"], w["fim"]) for w in windows] ==
            [(2010, 2014), (2015, 2019), (2020, 2024)], "Janelas diferentes do protocolo.")
    for window in windows:
        require(all(isinstance(window[p], int) and not isinstance(window[p], bool)
                    and window[p] >= 0 for p in PARTITIONS), "Quota inválida.")
        require(sum(window[p] for p in PARTITIONS) == window["total"],
                "Quotas da janela não somam seu total.")
    require(sum(w["total"] for w in windows) == 200, "Janelas não somam 200.")
    require(all(sum(w[p] for w in windows) == n for p, n in expected_partitions.items()),
            "Quotas das janelas não correspondem às partições.")
    rows, membership, source_manifest = read_source(archive)
    eligible = [row for row in rows if any(has_scope(code) for code in row["_codes"])]
    excluded = [row for row in rows if not any(has_scope(code) for code in row["_codes"])]
    selected = []
    windows_audit = {}
    for window in windows:
        label = f"{window['inicio']}-{window['fim']}"
        available = {p: [row for row in eligible
                         if membership[row["patent_id"]] == p
                         and window["inicio"] <= row["_year"] <= window["fim"]]
                     for p in PARTITIONS}
        windows_audit[label] = {
            "disponiveis_por_particao": {p: len(candidates) for p, candidates in available.items()},
            "selecionadas": window["total"],
            **{p: window[p] for p in PARTITIONS},
        }
        for part, candidates in available.items():
            require(len(candidates) >= window[part],
                    f"Famílias insuficientes em {label}/{part}: "
                    f"{len(candidates)} disponíveis, {window[part]} requeridas.")
            ranked = sorted(candidates, key=lambda row: (
                sha256(f"{seed}|{label}|{part}|{row['patent_id']}".encode("utf-8")),
                row["patent_id"],
            ))
            selected.extend((row, label, part) for row in ranked[:window[part]])

    require(len(selected) == len({r["patent_id"] for r, _, _ in selected}) == 200,
            "Seleção inconsistente ou famílias repetidas.")
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
    writer.writeheader()
    for row, label, part in selected:
        writer.writerow({
            "id_familia_docdb": row["patent_id"], "appln_id": row["appln_id"],
            "appln_auth": row["appln_auth"], "appln_nr": row["appln_nr"],
            "data_deposito": row["application_date"], "ano_deposito": row["_year"],
            "titulo": row["title"], "idioma_titulo": row["title_language"],
            "resumo": row["abstract"], "idioma_resumo": row["abstract_language"],
            "cpc_codes": json.dumps(row["_codes"], ensure_ascii=False, separators=(",", ":")),
            "cpc_proxy": row["cpc_primary"], "janela": label, "particao": part,
        })
    csv_bytes = buffer.getvalue().encode("utf-8")
    selected_rows = [r for r, _, _ in selected]
    train_labels = {r["cpc_primary"] for r, _, p in selected if p == "treino"}
    coverage = {}
    for part in PARTITIONS:
        part_rows = [r for r, _, p in selected if p == part]
        labels = Counter(r["cpc_primary"] for r in part_rows)
        coverage[part] = {
            "rotulos_distintos": len(labels), "rotulos_com_uma_familia": sum(n == 1 for n in labels.values()),
            "familias_com_rotulo_observado_no_treino": sum(r["cpc_primary"] in train_labels for r in part_rows),
            "familias_com_rotulo_nao_observado_no_treino": sum(r["cpc_primary"] not in train_labels for r in part_rows),
        }
    report = {
        "schema_version": "1.0", "piloto_id": pilot["id"],
        "sha256_entrada": source_hash, "sha256_piloto": sha256(csv_bytes),
        "membros_zip": {"csv": "patents_lora_1000_preview.csv", "manifesto": "manifest.json"},
        "manifesto_origem": source_manifest,
        "contagens": {"universo": len(rows), "elegiveis": len(eligible),
                       "excluidas_sem_cpc_a61_c12n": len(excluded), "selecionadas": len(selected)},
        "elegibilidade": {
            "campo": "cpc_codes", "regra": "qualquer CPC da família começa com A61 OU C12N",
            "prefixos": list(PREFIXES),
            "ipc_disponivel": False,
            "consulta_origem": "IPC A61 OU C12N OU C12Q; depósito ou inventor/depositante BR; 2010–2024",
            "interpretacao": "Recorte verificável por CPC da família dentro da base antiga; IPC original não foi exportado.",
            "c12q": "C12Q isoladamente não torna a família elegível; coexistência com A61/C12N é permitida.",
            "ids_excluidos": sorted((r["patent_id"] for r in excluded), key=int),
        },
        "amostragem": {
            "semente": seed,
            "ordem": "SHA256 UTF-8 de {semente}|{janela}|{particao}|{id_familia_docdb}; desempate por ID textual",
            "estratos": "janela temporal do depósito do representante e partição original",
            "particoes_originais_preservadas": True,
            "quotas_janelas": windows,
        },
        "janelas": windows_audit,
        "particoes": {p: {"total": sum(part == p for _, _, part in selected),
                           "com_cpc_proxy": sum(part == p and bool(r["cpc_primary"]) for r, _, part in selected)}
                      for p in PARTITIONS},
        "idiomas": {"formato": "idioma_titulo/idioma_resumo", "universo": language_counts(rows),
                    "elegiveis": language_counts(eligible), "piloto": language_counts(selected_rows)},
        "cobertura_cpc": coverage,
        "cpc_proxy": "Primeiro símbolo CPC da família em ordem alfanumérica, integral e sem remapeamento; não é CPC principal oficial.",
        "limites": [
            "Vínculo brasileiro decorre da consulta original; o país do pedido representante pode ser outro.",
            "Título e resumo foram escolhidos separadamente entre membros da família; IDs dos documentos textuais não foram retidos.",
            "appln_nr é número de pedido; número e data de publicação não estão disponíveis neste pacote.",
            "Edição PATSTAT e data da extração original não foram registradas.",
            "Representante temporal e textos podem provir de membros diferentes; não inferir disponibilidade histórica dos textos.",
            "200 famílias sustentam um piloto; frequências e indicadores temáticos são exploratórios.",
        ],
    }
    audit_bytes = (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return csv_bytes, audit_bytes, report


def write_outputs(directory: Path, csv_bytes: bytes, audit_bytes: bytes) -> None:
    """Preflight all outputs and refuse replacement of a different frozen result."""
    outputs = {directory / "piloto_200.csv": csv_bytes, directory / "auditoria.json": audit_bytes}
    for target, expected in outputs.items():
        if target.exists():
            require(target.is_file() and target.read_bytes() == expected,
                    f"Saída congelada divergente: {target}. Use outra pasta/versão após revisar a causa.")
    directory.mkdir(parents=True, exist_ok=True)
    for target, expected in outputs.items():
        if target.exists():
            continue
        with tempfile.NamedTemporaryFile(mode="wb", dir=directory, prefix=".selecao_", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(expected)
        try:
            # Preflight again before the final rename, without overwriting a differing file.
            if target.exists():
                require(target.read_bytes() == expected, f"Saída mudou durante a seleção: {target}.")
            else:
                temporary.rename(target)
        finally:
            temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", type=Path, required=True, help="ZIP original congelado de 1.000 famílias")
    parser.add_argument("--saida", type=Path, required=True, help="Diretório do piloto e auditoria")
    parser.add_argument("--config", type=Path, required=True, help="config/experimento.json")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8-sig"))
    csv_bytes, audit_bytes, report = build_outputs(args.entrada.read_bytes(), config)
    write_outputs(args.saida, csv_bytes, audit_bytes)
    print(json.dumps({"estado": "piloto_congelado", "pasta": str(args.saida),
                      "contagens": report["contagens"], "particoes": report["particoes"],
                      "sha256_piloto": report["sha256_piloto"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
