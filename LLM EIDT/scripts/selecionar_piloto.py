"""Seleciona famílias de uma nova exportação autorizada e congela o piloto localmente."""

import argparse
import csv
import hashlib
import json
import os
import re
import tempfile
from collections import Counter
from datetime import date
from itertools import chain
from pathlib import Path


CAMPOS = ("id_publicacao", "id_familia", "data_deposito", "data_publicacao",
          "titulo_zh", "resumo_zh", "cpc_principal")
PARTICOES = ("treino", "validacao", "teste")
CONFIG_PADRAO = Path(__file__).resolve().parents[1] / "config" / "experimento.json"
IDEOGRAMA = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U000323af]")
AUSENTES = {"", "na", "n/a", "nan", "null", "none", "-", "—"}


def resumo_arquivo(caminho):
    soma = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            soma.update(bloco)
    return soma.hexdigest()


def ler_janelas(config):
    plano = config["piloto"]["amostragem"]
    janelas = sorted(plano["janelas"], key=lambda item: item["inicio"])
    if not janelas or any(j["inicio"] > j["fim"] or
                          any(type(j[p]) != int or j[p] < 0 for p in PARTICOES) or
                          sum(j[p] for p in PARTICOES) != j["total"] for j in janelas):
        raise ValueError("Verifique intervalos, cotas e partições na configuração.")
    if any(a["fim"] >= b["inicio"] for a, b in zip(janelas, janelas[1:])):
        raise ValueError("As janelas do piloto se sobrepõem.")
    if plano["total"] != 200 or sum(j["total"] for j in janelas) != plano["total"]:
        raise ValueError("As cotas da configuração devem totalizar 200 famílias.")
    return plano["semente"], janelas


def data_iso(texto):
    # Quatro dígitos de ano no início evitam ambiguidade entre dia e mês.
    if re.fullmatch(r"\d{8}", texto):
        texto = f"{texto[:4]}-{texto[4:6]}-{texto[6:]}"
    texto = texto.replace("/", "-")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", texto):
        raise ValueError("Data com formato desconhecido.")
    return date.fromisoformat(texto).isoformat()


def cabecalhos(leitor, mapa):
    nomes = leitor.fieldnames
    if not nomes or len(nomes) != len(set(nomes)) or "" in nomes:
        raise ValueError("O cabeçalho CSV está vazio ou contém nomes de colunas repetidos.")
    if not isinstance(mapa, dict) or set(mapa) - set(CAMPOS):
        raise ValueError("O mapa deve ser um objeto de campo canônico para nome da coluna.")
    colunas = {campo: mapa.get(campo, campo) for campo in CAMPOS}
    if not all(isinstance(v, str) and v for v in colunas.values()):
        raise ValueError("Os nomes das colunas no mapa devem ser textos não vazios.")
    if len(set(colunas.values())) != len(colunas):
        raise ValueError("O mapa atribui uma coluna de origem a mais de um campo.")
    obrigatorias = set(CAMPOS[:-1]) | set(mapa)
    faltam = [colunas[k] for k in sorted(obrigatorias) if colunas[k] not in nomes]
    if faltam:
        raise ValueError("Colunas ausentes na exportação: " + ", ".join(faltam))
    return colunas


def ler_familias(entrada, mapa, janelas):
    totais = Counter()
    exclusoes = Counter()
    representantes = {}
    publicacoes = {}
    soma = hashlib.sha256()
    csv.field_size_limit(16 * 1024 * 1024)
    with entrada.open("rb") as fluxo:
        primeira_linha = fluxo.readline()
        try:
            delimitador = csv.Sniffer().sniff(primeira_linha.decode("utf-8-sig"), delimiters=",;\t").delimiter
        except csv.Error as erro:
            raise ValueError("O cabeçalho deve ser separado por vírgula, ponto e vírgula ou tabulação.") from erro
        # Usar o mesmo fluxo para ler as patentes e assinar os bytes, inclusive BOM e fins de linha.
        def linhas():
            for i, bloco in enumerate(chain((primeira_linha,), fluxo)):
                soma.update(bloco)
                yield bloco.decode("utf-8" if i else "utf-8-sig")

        leitor = csv.DictReader(linhas(), delimiter=delimitador, strict=True)
        colunas = cabecalhos(leitor, mapa)
        for linha in leitor:
            totais["linhas_lidas"] += 1
            if None in linha or None in linha.values():
                raise ValueError(f"Número de colunas inválido perto da linha física {leitor.line_num}.")
            registro = {k: linha.get(v, "").strip() for k, v in colunas.items()}
            for campo in CAMPOS:
                if registro[campo].casefold() in AUSENTES:
                    registro[campo] = ""
            if not all(registro[k] for k in CAMPOS[:-1]):
                exclusoes["campos_obrigatorios_vazios"] += 1
                continue
            try:
                for k in ("data_deposito", "data_publicacao"):
                    registro[k] = data_iso(registro[k])
            except ValueError:
                exclusoes["datas_invalidas"] += 1
                continue
            if registro["data_publicacao"] < registro["data_deposito"]:
                exclusoes["publicacao_antes_do_deposito"] += 1
                continue
            ano = int(registro["data_deposito"][:4])
            janela = next((j for j in janelas if j["inicio"] <= ano <= j["fim"]), None)
            if janela is None:
                exclusoes["deposito_fora_das_janelas"] += 1
                continue
            if not all(IDEOGRAMA.search(registro[k]) for k in ("titulo_zh", "resumo_zh")):
                exclusoes["sem_ideograma_em_titulo_ou_resumo"] += 1
                continue
            id_pub = registro["id_publicacao"]
            assinatura = hashlib.sha256(json.dumps(registro, ensure_ascii=False).encode("utf-8")).digest()
            if id_pub in publicacoes:
                if publicacoes[id_pub] != assinatura:
                    raise ValueError(f"Publicação {id_pub!r} tem registros conflitantes entre linhas elegíveis. Revise a fonte.")
                totais["linhas_elegiveis_repetidas"] += 1
                continue
            publicacoes[id_pub] = assinatura
            registro["janela"] = f"{janela['inicio']}-{janela['fim']}"
            familia = registro["id_familia"]
            chave = (registro["data_deposito"], registro["data_publicacao"], id_pub)
            if familia not in representantes or chave < representantes[familia][0]:
                representantes[familia] = (chave, registro)
    totais["publicacoes_elegiveis_distintas"] = len(publicacoes)
    totais["familias_elegiveis_distintas"] = len(representantes)
    return [r for _, r in representantes.values()], dict(totais), dict(exclusoes), soma.hexdigest(), colunas


def chave_sorteio(registro, semente, finalidade):
    familia = registro["id_familia"]
    texto = json.dumps([semente, finalidade, registro["janela"], familia],
                       ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(texto.encode("utf-8")).digest(), familia


def selecionar(entrada, saida, config=CONFIG_PADRAO, mapa=None):
    entrada = Path(entrada).absolute()
    saida = Path(saida).absolute()
    configuracao = Path(config).read_bytes()
    semente, janelas = ler_janelas(json.loads(configuracao.decode("utf-8-sig")))
    colunas = json.loads(Path(mapa).read_text("utf-8-sig")) if mapa else {}
    familias, totais, exclusoes, sha_entrada, colunas = ler_familias(entrada, colunas, janelas)
    amostra = []
    cobertura = {}
    particoes = {p: {"total": 0, "com_cpc_principal": 0} for p in PARTICOES}
    for janela in janelas:
        nome = f"{janela['inicio']}-{janela['fim']}"
        grupo = [r for r in familias if r["janela"] == nome]
        n = janela["total"]
        if len(grupo) < n:
            raise ValueError(f"{nome} exige {n} famílias elegíveis e só há {len(grupo)}. "
                             f"Exclusões por motivo: {exclusoes}. Amplie a exportação e repita.")
        sorteados = sorted(grupo, key=lambda r: chave_sorteio(r, semente, "amostra"))[:n]
        sorteados.sort(key=lambda r: chave_sorteio(r, semente, "particao"))
        cobertura[nome] = {"familias_elegiveis": len(grupo), "selecionadas": n,
                           **{p: janela[p] for p in PARTICOES}}
        inicio = 0
        for particao in PARTICOES:
            fim = inicio + janela[particao]
            bloco = sorteados[inicio:fim]
            amostra.extend({**r, "particao": particao} for r in bloco)
            particoes[particao]["total"] += len(bloco)
            particoes[particao]["com_cpc_principal"] += sum(bool(r["cpc_principal"]) for r in bloco)
            inicio = fim
    saida.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".selecionando_", dir=saida.parent) as temporario:
        lote = Path(temporario) / "lote"
        lote.mkdir()
        arquivo = lote / "piloto_200.csv"
        with arquivo.open("w", encoding="utf-8", newline="") as csv_saida:
            escritor = csv.DictWriter(csv_saida, fieldnames=(*CAMPOS, "janela", "particao"), lineterminator="\n")
            escritor.writeheader()
            escritor.writerows(amostra)
        completo = all(p["total"] == p["com_cpc_principal"] for p in particoes.values())
        auditoria = {
            "formato": 1, "sha256_entrada": sha_entrada, "sha256_piloto": resumo_arquivo(arquivo),
            "sha256_config": hashlib.sha256(configuracao).hexdigest(),
            "sha256_seletor": resumo_arquivo(Path(__file__)), "colunas": colunas, "semente": semente,
            "totais": totais, "exclusoes_por_primeiro_motivo": exclusoes,
            "janelas": cobertura, "particoes": particoes,
            "status_cpc": "cobertura_completa_a_validar" if completo else "supervisao_pendente_cpc",
            "criterio_cpc": "A presença mede preenchimento. Conferir origem, nível e unicidade do CPC principal antes do ajuste e da avaliação. O CPC não interfere na seleção.",
            "representante": "Entre publicações elegíveis nas três janelas, escolher por família a de menor (depósito, publicação, ID). Aceitar IDs opacos, sensíveis a maiúsculas, após retirar espaços das pontas.",
            "texto": "Título e resumo precisam conter ideograma CJK. A língua, o domínio científico, o país e o tipo de invenção devem ser confirmados na exportação de origem.",
            "amostragem": "Ordenar SHA-256 do JSON compacto UTF-8 [semente, finalidade, janela, ID de família]. Separar sorteios com finalidades amostra e particao. Desempatar pelo ID de família.",
            "limite": "Piloto de engenharia com alocação por janela. Avaliar novidade e anterioridade requer um histórico mais amplo.",
        }
        nome_auditoria = "auditoria.json"
        (lote / nome_auditoria).write_text(json.dumps(auditoria, ensure_ascii=False, indent=2,
                                                     sort_keys=True) + "\n", encoding="utf-8")
        # A publicação do diretório completo evita deixar um CSV sem seu relatório.
        if saida.exists():
            if not saida.is_dir():
                raise ValueError("A saída deve ser uma pasta exclusiva do piloto.")
            if any(saida.iterdir()):
                nomes = {arquivo.name, nome_auditoria}
                if {p.name for p in saida.iterdir()} == nomes and all(
                    (saida / n).is_file() and resumo_arquivo(saida / n) == resumo_arquivo(lote / n) for n in nomes
                ):
                    return auditoria
                raise ValueError("A pasta de saída já contém outro resultado ou arquivos incompletos. Use uma nova pasta.")
            # Windows não renomeia um diretório sobre um diretório existente. rmdir exige pasta vazia.
            saida.rmdir()
        os.rename(lote, saida)
    return auditoria


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", required=True, type=Path, help="Nova exportação CSV em UTF-8.")
    parser.add_argument("--saida", required=True, type=Path, help="Pasta exclusiva desta seleção.")
    parser.add_argument("--mapa", type=Path, help="JSON opcional de campo canônico para cabeçalho de origem.")
    parser.add_argument("--config", type=Path, default=CONFIG_PADRAO, help="Configuração de experimento do piloto.")
    args = parser.parse_args()
    try:
        auditoria = selecionar(args.entrada, args.saida, args.config, args.mapa)
    except (OSError, ValueError, KeyError, TypeError, csv.Error) as erro:
        parser.exit(2, f"Seleção interrompida: {erro}\n")
    print(f"200 famílias em {args.saida}. CPC: {auditoria['status_cpc']}.")
    print(f"SHA-256 do piloto: {auditoria['sha256_piloto']}")


if __name__ == "__main__":
    main()
