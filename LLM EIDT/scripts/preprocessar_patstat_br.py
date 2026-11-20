"""Prepare textos PATSTAT pt/en e valide extrações com evidência rastreável.

O pré-processamento não executa modelos nem produz rótulos de extração.
Uma falha de geração/validação deve permanecer falha, nunca seis listas vazias.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import unicodedata
from pathlib import Path


VERSAO_SCHEMA = "patstat-br-extracao-1.0"
PARTICOES = ("treino", "validacao", "teste")
GRUPOS = ("memes_tecnicos", "pares_convergencia", "funcoes", "materiais", "processos", "efeitos")
CAMPOS_CSV = {
    "id_familia_docdb", "appln_id", "appln_auth", "appln_nr", "data_deposito",
    "ano_deposito", "titulo", "idioma_titulo", "resumo", "idioma_resumo",
    "cpc_codes", "cpc_proxy", "janela", "particao",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalizar(texto: str) -> str:
    """NFC e quebras LF. Preserva caixa, acentos, espaços e conteúdo."""
    return unicodedata.normalize("NFC", texto.replace("\r\n", "\n").replace("\r", "\n"))


def json_bytes(objeto: object, *, identado: bool = False) -> bytes:
    return (json.dumps(objeto, ensure_ascii=False, sort_keys=True,
                       indent=2 if identado else None) + "\n").encode("utf-8")


def jsonl_bytes(linhas: list[dict]) -> bytes:
    return b"".join(json_bytes(linha) for linha in linhas)


def carregar_schema(caminho: Path | None = None) -> dict:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise RuntimeError("Instale jsonschema==4.25.1 antes de preparar ou validar os dados.") from exc
    if caminho is None:
        caminho = Path(__file__).absolute().parent.parent / "schemas/extracao_patstat_br.schema.json"
    schema = json.loads(Path(caminho).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def validar_extracao(payload: dict, entrada: dict, schema_path: Path | None = None) -> None:
    """Valida estrutura, identidade, referências e citações; lança ValueError.

    Os índices de evidência usam pontos de código Unicode Python, início
    inclusivo e fim exclusivo, sobre entrada['textos'][campo]. A validade
    semântica da relação alegada continua dependente da anotação humana.
    """
    from jsonschema import Draft202012Validator

    schema = carregar_schema(schema_path)
    erros = sorted(Draft202012Validator(schema).iter_errors(payload),
                   key=lambda erro: str(list(erro.absolute_path)))
    if erros:
        erro = erros[0]
        raise ValueError(f"JSON fora do schema em {list(erro.absolute_path)}: {erro.message}")
    if payload["id_familia_docdb"] != entrada["id_familia_docdb"]:
        raise ValueError("Identificador de família diferente da entrada.")
    if payload["idiomas_entrada"] != entrada["idiomas"]:
        raise ValueError("Idiomas declarados diferentes dos metadados da entrada.")

    identificadores = set()
    memes = {item["id"] for item in payload["memes_tecnicos"]}
    elementos = {item["id"] for grupo in ("memes_tecnicos", "funcoes", "materiais", "processos")
                 for item in payload[grupo]}
    pares = set()
    for grupo in GRUPOS:
        for item in payload[grupo]:
            if item["id"] in identificadores:
                raise ValueError(f"Identificador repetido: {item['id']}.")
            identificadores.add(item["id"])
            idiomas_evidencia = set()
            for evidencia in item["evidencias"]:
                campo = evidencia["campo"]
                texto = entrada["textos"][campo]
                inicio, fim = evidencia["inicio"], evidencia["fim"]
                if not (0 <= inicio < fim <= len(texto)):
                    raise ValueError(f"Intervalo de evidência inválido em {item['id']}.")
                if texto[inicio:fim] != evidencia["texto"]:
                    raise ValueError(f"Evidência não corresponde ao trecho original normalizado em {item['id']}.")
                if evidencia["idioma"] != entrada["idiomas"][campo]:
                    raise ValueError(f"Idioma da evidência diverge do campo em {item['id']}.")
                idiomas_evidencia.add(evidencia["idioma"])
            if "idioma" in item and item["idioma"] not in idiomas_evidencia:
                raise ValueError(f"Idioma do elemento sem evidência correspondente em {item['id']}.")
            if grupo == "pares_convergencia":
                if not set(item["memes"]).issubset(memes):
                    raise ValueError(f"Par referencia meme inexistente em {item['id']}.")
                par = tuple(sorted(item["memes"]))
                if par in pares:
                    raise ValueError("Par de convergência duplicado, inclusive em ordem inversa.")
                pares.add(par)
            if grupo == "efeitos" and not set(item["relacionado_a"]).issubset(elementos):
                raise ValueError(f"Efeito referencia elemento inexistente em {item['id']}.")


def construir_mensagens(entrada: dict, prompt_path: Path | None = None) -> list[dict]:
    """Monta entrada de extração sem CPC, partição ou metadados de avaliação."""
    if prompt_path is None:
        prompt_path = Path(__file__).absolute().parent.parent / "prompts/extracao_patstat_br.txt"
    dados = {chave: entrada[chave] for chave in ("id_familia_docdb", "idiomas", "textos")}
    return [
        {"role": "system", "content": Path(prompt_path).read_text(encoding="utf-8")},
        {"role": "user", "content": "DADOS_DA_PATENTE_JSON\n" + json.dumps(dados, ensure_ascii=False)
         + "\nFIM_DOS_DADOS_DA_PATENTE_JSON"},
    ]


def preparar(entrada: Path, saida: Path, config_path: Path) -> dict:
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    opcoes = config["piloto"].get("preprocessamento", {})
    idiomas_permitidos = set(opcoes.get("idiomas_permitidos", ["pt", "en"]))
    if idiomas_permitidos != {"pt", "en"}:
        raise ValueError("Este protocolo validado aceita exatamente pt e en; revisão exige outro protocolo.")
    raiz = config_path.absolute().parent.parent
    schema_path = raiz / opcoes.get("schema_extracao", "schemas/extracao_patstat_br.schema.json")
    prompt_path = raiz / opcoes.get("prompt_extracao", "prompts/extracao_patstat_br.txt")
    carregar_schema(schema_path)
    if not prompt_path.is_file():
        raise ValueError(f"Prompt ausente: {prompt_path}")
    dados_bytes = entrada.read_bytes()
    auditoria_path = raiz / config["piloto"]["amostragem"]["auditoria"]
    auditoria_bytes = auditoria_path.read_bytes()
    auditoria_selecao = json.loads(auditoria_bytes)
    if auditoria_selecao.get("sha256_piloto") != sha256(dados_bytes):
        raise ValueError("O CSV mudou após a seleção ou não corresponde à auditoria congelada.")
    if auditoria_selecao.get("sha256_entrada") != config["piloto"]["coleta"]["sha256_zip"]:
        raise ValueError("A auditoria de seleção pertence a outro pacote PATSTAT.")
    with entrada.open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        faltantes = CAMPOS_CSV - set(leitor.fieldnames or [])
        if faltantes:
            raise ValueError(f"Colunas ausentes: {sorted(faltantes)}")
        linhas = list(leitor)

    extracoes, metadados = [], []
    cpc_por_particao = {particao: [] for particao in PARTICOES}
    ids = set()
    pares_idiomas = collections.Counter()
    normalizados = collections.Counter()
    contagens_janelas = collections.Counter()
    for linha in linhas:
        familia = linha["id_familia_docdb"]
        if not familia.isdigit() or int(familia) <= 0 or familia in ids:
            raise ValueError(f"Família inválida ou duplicada: {familia}")
        ids.add(familia)
        particao = linha["particao"]
        if particao not in PARTICOES:
            raise ValueError(f"Partição inválida: {particao}")
        idiomas = {campo: linha[f"idioma_{campo}"] for campo in ("titulo", "resumo")}
        if not set(idiomas.values()).issubset(idiomas_permitidos):
            raise ValueError(f"Idioma sem suporte na família {familia}: {idiomas}")
        originais = {campo: linha[campo] for campo in ("titulo", "resumo")}
        if any(not texto.strip() or texto.strip().lower() in {"nan", "none", "null"}
               for texto in originais.values()):
            raise ValueError(f"Título ou resumo vazio na família {familia}.")
        textos = {campo: normalizar(texto) for campo, texto in originais.items()}
        for campo in textos:
            normalizados[campo] += int(textos[campo] != originais[campo])
        codigos = json.loads(linha["cpc_codes"])
        if not isinstance(codigos, list) or not codigos or any(not isinstance(c, str) or not c for c in codigos):
            raise ValueError(f"Lista CPC inválida na família {familia}.")
        if linha["cpc_proxy"] != sorted(set(codigos))[0]:
            raise ValueError(f"Proxy CPC não segue a regra alfabética na família {familia}.")
        registro = {
            "id_familia_docdb": familia, "particao": particao, "janela": linha["janela"],
            "idiomas": idiomas, "textos": textos,
            "sha256_textos_normalizados": sha256(json_bytes(textos)),
        }
        extracoes.append(registro)
        metadados.append({
            "id_familia_docdb": familia,
            "representante_familia": {chave: linha[chave] for chave in
                                     ("appln_id", "appln_auth", "appln_nr", "data_deposito", "ano_deposito")},
            "origem_textos": {"appln_id_titulo": None, "appln_id_resumo": None,
                              "coerencia_com_representante": "nao_verificavel_no_pacote"},
            "publicacao": {"id": None, "data": None},
            "textos_originais": originais, "idiomas": idiomas,
            "sha256_textos_normalizados": registro["sha256_textos_normalizados"],
            "particao": particao, "janela": linha["janela"],
            "cpc_codes": codigos, "cpc_proxy": linha["cpc_proxy"],
            "regra_cpc_proxy": "primeiro símbolo CPC da família em ordem alfanumérica",
        })
        cpc_por_particao[particao].append({
            "id_familia_docdb": familia, "particao": particao, "janela": linha["janela"],
            "entrada": {"textos": textos, "idiomas": idiomas},
            "alvo_cpc_proxy": linha["cpc_proxy"],
        })
        pares_idiomas[f"{idiomas['titulo']}/{idiomas['resumo']}"] += 1
        contagens_janelas[linha["janela"]] += 1
    esperado = config["piloto"]["amostragem"]
    if len(linhas) != esperado["total"]:
        raise ValueError("A quantidade de famílias diverge do protocolo congelado.")
    contagens = {particao: len(cpc_por_particao[particao]) for particao in PARTICOES}
    if contagens != esperado["particoes"]:
        raise ValueError(f"As partições divergem do protocolo: {contagens}.")
    arquivos = {
        "entradas_extracao.jsonl": jsonl_bytes(extracoes),
        "metadados.jsonl": jsonl_bytes(metadados),
        **{f"{particao}_cpc.jsonl": jsonl_bytes(cpc_por_particao[particao]) for particao in PARTICOES},
    }
    relatorio = {
        "protocolo": config["protocolo"]["id"], "schema_extracao": VERSAO_SCHEMA,
        "estado": "entradas_preparadas_sem_execucao_de_modelo",
        "sha256_entrada": sha256(dados_bytes), "sha256_config": sha256(config_bytes),
        "sha256_auditoria_selecao": sha256(auditoria_bytes),
        "sha256_schema": sha256(schema_path.read_bytes()), "sha256_prompt": sha256(prompt_path.read_bytes()),
        "total_familias": len(ids), "particoes": contagens,
        "janelas": dict(sorted(contagens_janelas.items())), "pares_idiomas": dict(sorted(pares_idiomas.items())),
        "campos_alterados_por_normalizacao": dict(normalizados), "campos_vazios": 0,
        "normalizacao": "Unicode NFC e quebras LF; texto original preservado em metadados.jsonl",
        "traducao": "nao_aplicada", "origem_textos": "aplicações fonte de título e resumo não registradas",
        "cpc_no_prompt_extracao": False,
        "tokens": {"estado": "pendente_tokenizador_Qwen3", "recorte": "nao_aplicado_nesta_etapa"},
        "validacao_futura": "Preservar retorno bruto e erro. JSON inválido ou interrompido não conta como ausência de evidência.",
        "sha256_arquivos": {nome: sha256(conteudo) for nome, conteudo in sorted(arquivos.items())},
    }
    arquivos["auditoria_preprocessamento.json"] = json_bytes(relatorio, identado=True)
    for nome, conteudo in arquivos.items():
        destino = saida / nome
        if destino.exists() and destino.read_bytes() != conteudo:
            raise FileExistsError(f"Saída diferente já existe: {destino}. Use outro diretório de execução.")
    saida.mkdir(parents=True, exist_ok=True)
    for nome, conteudo in arquivos.items():
        destino = saida / nome
        if not destino.exists():
            with destino.open("xb") as arquivo:
                arquivo.write(conteudo)
    return relatorio


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    try:
        relatorio = preparar(args.entrada, args.saida, args.config)
    except (ValueError, OSError, RuntimeError, KeyError) as erro:
        parser.exit(1, f"Pré-processamento interrompido: {erro}\n")
    print(json.dumps({"estado": relatorio["estado"], "total_familias": relatorio["total_familias"],
                      "particoes": relatorio["particoes"], "pares_idiomas": relatorio["pares_idiomas"]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
