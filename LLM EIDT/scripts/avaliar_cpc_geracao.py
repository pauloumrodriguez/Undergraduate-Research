"""Comparação exploratória de geração CPC: base e LoRA, somente 20 validações.

Sem treinamento e sem acesso à partição teste. O checkpoint e o protocolo são
conferidos antes do carregamento. Funções de integridade são importáveis sem GPU.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import csv
from datetime import datetime, timezone
from importlib import metadata
import io
import json
import math
import os
from pathlib import Path
import random
import re
import sys
import time
import unicodedata

import testar_qlora_gpu as helper
import treinar_qlora_cpc as training

PROFILE_ID = "br_patstat_200_qwen3_8b_cpc_validacao_v1"
RESULTS = "resultados/etapa_3/piloto_br_200"
CPC_PATTERN = r"[A-HY][0-9]{2}[A-Z][0-9]{1,4}/[0-9]{2,6}"
GENERATION = {"max_prompt_tokens": 992, "max_new_tokens": 32, "contexto_total": 1024,
              "do_sample": False, "num_beams": 1, "use_cache": True, "enable_thinking": False}
ORIGIN_KEYS = ("config", "perfil_treino", "auditoria_preprocessamento", "validacao",
               "relatorio_treino", "preparacao_treino", "helper_teste", "helper_treino")
require, sha256 = helper.require, helper.sha256


def canonical_cpc(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", value).upper())


def preflight(root: Path, profile: dict) -> dict:
    """Read validation/provenance/checkpoint only; no train/test data or torch.load."""
    require(profile["id"] == PROFILE_ID and profile["resultados"] == RESULTS, "Perfil de avaliação desconhecido.")
    require(profile["geracao"] == GENERATION and profile["semente"] == 42, "Decodificação diverge do protocolo.")
    evaluation = profile["avaliacao"]
    require(evaluation["particao"] == "validacao" and evaluation["familias"] == 20
            and evaluation["variantes"] == ["base", "adaptado"] and evaluation["regex_cpc"] == CPC_PATTERN
            and evaluation["exigir_eos"] is True, "Avaliação deve usar as 20 famílias de validação.")
    origin = profile["origem"]
    contents = {key: training.checked(root, origin, key) for key in ORIGIN_KEYS}
    require(sha256(Path(helper.__file__).read_bytes()) == origin["sha256_helper_teste"]
            and sha256(Path(training.__file__).read_bytes()) == origin["sha256_helper_treino"],
            "As dependências importadas diferem da versão congelada.")
    base = json.loads(contents["config"])
    train_profile = json.loads(contents["perfil_treino"])
    audit = json.loads(contents["auditoria_preprocessamento"])
    report = json.loads(contents["relatorio_treino"])
    preparation = json.loads(contents["preparacao_treino"])
    require(profile["modelo"] == train_profile["modelo"]
            and all(profile["modelo"][key] == base["modelos"]["qwen"][key] for key in ("id", "revisao")),
            "Modelo/revisão diverge do treinamento.")
    require(profile["quantizacao"] == train_profile["quantizacao"] ==
            {"tipo": "nf4", "double_quant": True, "compute_dtype": "float16"}, "Quantização divergente.")
    require(report["perfil"] == train_profile and report["sha256_perfil"] == origin["sha256_perfil_treino"],
            "Relatório pertence a outro perfil de treinamento.")
    require(report["estado"] == "treino_qlora_concluido" and report["etapa"] == "concluido"
            and not report.get("erro") and not report.get("etapa_falha")
            and report["passos_concluidos"] == 30 and report["epocas_concluidas"] == 3,
            "O treinamento não foi concluído nas condições previstas.")
    require(report["teste_executado"] is False and report["selecao"]["teste_executado"] is False,
            "Relatório indica uso da partição reservada.")
    require(preparation["estado"] == "treino_concluido" and preparation["codigo_saida"] == 0
            and not preparation["interrompido"] and preparation["perfil"] == train_profile["id"],
            "Preparação do notebook 05 não confirma conclusão.")
    require(preparation["relatorio_treino"] == origin["relatorio_treino"]
            and preparation["sha256_diagnostico"] == report["origem"]["sha256_diagnostico"]
            == report["compatibilidade"]["sha256_diagnostico"], "Relatórios 05 inconsistentes.")
    for key in ("config", "auditoria_preprocessamento", "validacao"):
        require(origin[key] == train_profile["origem"][key]
                and origin["sha256_" + key] == train_profile["origem"]["sha256_" + key], "Origem divergente: " + key)
    for key in ("config", "perfil_treino", "auditoria_preprocessamento", "validacao", "helper_teste", "helper_treino"):
        require(preparation["sha256_arquivos"].get(origin[key]) == origin["sha256_" + key],
                "Hash não confirmado pela preparação 05: " + key)
    require(report["compatibilidade"]["sha256_script"] == origin["sha256_helper_treino"]
            and report["compatibilidade"]["sha256_perfil"] == origin["sha256_perfil_treino"]
            and report["compatibilidade"]["origem"] == train_profile["origem"], "Compatibilidade 05 divergente.")
    require(audit["sha256_config"] == origin["sha256_config"]
            and audit["sha256_arquivos"]["validacao_cpc.jsonl"] == origin["sha256_validacao"]
            and audit["particoes"] == {"treino": 160, "validacao": 20, "teste": 20}, "Auditoria divergente.")
    records = [json.loads(line) for line in contents["validacao"].decode("utf-8").splitlines() if line.strip()]
    require(len(records) == 20, "Esperadas 20 famílias.")
    identifiers = set()
    for record in records:
        family = record["id_familia_docdb"]
        require(isinstance(family, str) and family.isdigit() and int(family) > 0 and family not in identifiers,
                "Identificador inválido ou duplicado.")
        identifiers.add(family)
        require(record["particao"] == "validacao", "Outra partição encontrada na avaliação.")
        require(bool(re.fullmatch(CPC_PATTERN, canonical_cpc(record["alvo_cpc_proxy"]))), "Alvo CPC fora do formato fixado.")
        for field in ("titulo", "resumo"):
            require(record["entrada"]["idiomas"][field] in {"pt", "en"}
                    and bool(record["entrada"]["textos"][field].strip()), "Texto/idioma inválido.")
    epochs = report["historico_epocas"]
    require([entry["epoca"] for entry in epochs] == [1, 2, 3]
            and all(math.isfinite(entry["validacao"]["loss"]) for entry in epochs), "Histórico inválido.")
    best = min(epochs, key=lambda entry: (entry["validacao"]["loss"], entry["epoca"]))
    checkpoint = profile["checkpoint"]
    require(checkpoint["epoca"] == best["epoca"] == report["melhor_epoca"] == report["selecao"]["epoca"] == 3
            and checkpoint["passo"] == 30 and checkpoint["diretorio"] == best["checkpoint"]
            == report["selecao"]["checkpoint"] and report["adaptador_selecionado"] == checkpoint["diretorio"] + "/adapter"
            and report["selecao"]["validacao_loss"] == best["validacao"]["loss"], "Checkpoint não corresponde à seleção fixada.")
    directory = training.safe_path(root, checkpoint["diretorio"])
    require(sha256((directory / "manifest.json").read_bytes()) == checkpoint["sha256_manifest"]
            == report["selecao"]["sha256_manifest_checkpoint"], "Manifesto do checkpoint divergente.")
    directory, envelope = training.verify_checkpoint(root, checkpoint["diretorio"], report["compatibilidade"])
    require(envelope["progresso"] == report["progresso"], "Progresso do checkpoint não corresponde ao relatório.")
    adapter = json.loads((directory / "adapter/adapter_config.json").read_bytes())
    lora = train_profile["lora"]
    require(adapter["base_model_name_or_path"] == profile["modelo"]["id"]
            and adapter["peft_type"] == "LORA" and adapter["task_type"] == "CAUSAL_LM"
            and adapter["r"] == lora["r"] and adapter["lora_alpha"] == lora["alpha"]
            and adapter["lora_dropout"] == lora["dropout"]
            and set(adapter["target_modules"]) == set(lora["target_modules"])
            and adapter["bias"] == "none" and adapter["inference_mode"] is True,
            "Configuração do adaptador é incompatível.")
    return {"records": sorted(records, key=lambda row: int(row["id_familia_docdb"])),
            "training_report": report, "training_profile": train_profile,
            "checkpoint_directory": directory,
            "provenance": {"hashes_origem": {key: origin["sha256_" + key] for key in ORIGIN_KEYS},
                "sha256_manifest_checkpoint": checkpoint["sha256_manifest"], "particao": "validacao",
                "teste_aberto": False, "treino_aberto": False,
                "nota": "Diagnóstico na validação usada para seleção; não é avaliação final independente."}}


def build_prompt(tokenizer, entrada: dict, maximum: int = 992) -> dict:
    """Only title/abstract/languages enter this function; never the CPC target."""
    payload = {"idiomas": entrada["idiomas"], "titulo": entrada["textos"]["titulo"],
               "resumo": entrada["textos"]["resumo"]}
    messages = [{"role": "system", "content": helper.SYSTEM_CPC},
                {"role": "user", "content": "DADOS_DA_PATENTE_JSON\n" + json.dumps(payload, ensure_ascii=False)
                 + "\nFIM_DOS_DADOS_DA_PATENTE_JSON"}]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    require(0 < len(ids) <= maximum, "Prompt excede o limite: revisar o protocolo, sem recorte automático.")
    return {"texto": prompt, "input_ids": ids, "attention_mask": [1] * len(ids),
            "sha256_prompt": sha256(prompt.encode("utf-8")), "tokens": len(ids)}


def score_prediction(tokenizer, generated: list[int], target: str, maximum: int = 32) -> dict:
    require(0 < len(generated) <= maximum, "Quantidade de tokens gerados inválida.")
    eos = bool(generated[-1] == tokenizer.eos_token_id)
    content = generated[:-1] if eos else generated
    raw = tokenizer.decode(generated, skip_special_tokens=False, clean_up_tokenization_spaces=False)
    text = tokenizer.decode(content, skip_special_tokens=False, clean_up_tokenization_spaces=False)
    canonical = canonical_cpc(text)
    unexpected_special = any(token in set(tokenizer.all_special_ids) for token in content)
    valid = bool(re.fullmatch(CPC_PATTERN, canonical)) and not unexpected_special
    expected = canonical_cpc(target)
    require(bool(re.fullmatch(CPC_PATTERN, expected)), "Alvo CPC inválido.")
    return {"ids_gerados": generated, "texto_bruto": raw, "texto_avaliado": text,
            "codigo_normalizado": canonical if valid else None, "alvo_cpc_proxy": target,
            "alvo_normalizado": expected, "tokens_gerados": len(generated), "terminou_em_eos": eos,
            "atingiu_limite": len(generated) == maximum and not eos,
            "formato_sintatico_valido": valid, "especial_inesperado": unexpected_special,
            "acerto_exato": bool(eos and valid and canonical == expected)}


def summarize(predictions: list[dict], expected_ids: list[str]) -> tuple[dict, dict]:
    require(len(expected_ids) == 20 and len(set(expected_ids)) == 20, "Coorte de avaliação inválida.")
    require(len(predictions) == 40, "Métricas finais exigem as 40 gerações completas.")
    lookup = {}
    for item in predictions:
        key = (item["variante"], item["id_familia_docdb"])
        require(key not in lookup and key[0] in {"base", "adaptado"} and key[1] in expected_ids,
                "Predição duplicada ou fora da coorte.")
        lookup[key] = item
    metrics = {}
    for variant in ("base", "adaptado"):
        rows = [lookup[(variant, family)] for family in expected_ids]
        correct = sum(row["acerto_exato"] for row in rows)
        valid = sum(row["formato_sintatico_valido"] for row in rows)
        metrics[variant] = {"familias": 20, "acertos_exatos": correct, "acuracia_exata": correct / 20,
            "formatos_sintaticos_validos": valid, "taxa_formato_sintatico": valid / 20,
            "terminacoes_eos": sum(row["terminou_em_eos"] for row in rows),
            "limites_atingidos": sum(row["atingiu_limite"] for row in rows)}
    paired = {"ambos_corretos": 0, "somente_base_correto": 0, "somente_adaptado_correto": 0, "ambos_incorretos": 0}
    for family in expected_ids:
        base, adapted = (lookup[(variant, family)]["acerto_exato"] for variant in ("base", "adaptado"))
        key = "ambos_corretos" if base and adapted else "somente_base_correto" if base else "somente_adaptado_correto" if adapted else "ambos_incorretos"
        paired[key] += 1
    paired["delta_acuracia_adaptado_menos_base"] = metrics["adaptado"]["acuracia_exata"] - metrics["base"]["acuracia_exata"]
    return metrics, paired


def generate_one(torch, model, tokenizer, prompt: dict, variant: str, device: str = "cuda:0", amp_dtype=None) -> list[int]:
    """Generate only from prompt; adapter toggle is checked and then restored."""
    from transformers import GenerationConfig
    require(variant in {"base", "adaptado"}, "Variante desconhecida.")
    status = model.get_model_status()
    require(status.enabled is True and status.merged_adapters == [], "Adaptador deve estar ativo e não mesclado.")
    options = GenerationConfig(do_sample=False, num_beams=1, max_new_tokens=32, use_cache=True,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id,
        bos_token_id=tokenizer.bos_token_id, return_dict_in_generate=False, output_scores=False)
    batch = {key: torch.tensor([prompt[key]], dtype=torch.long, device=device) for key in ("input_ids", "attention_mask")}
    context = model.disable_adapter() if variant == "base" else nullcontext()
    try:
        with context:
            require(model.get_model_status().enabled is (variant == "adaptado"), "Falha ao alternar os adaptadores.")
            with torch.inference_mode(), training.amp_context(torch, device, amp_dtype):
                result = model.generate(**batch, generation_config=options)
            full = result[0].detach().cpu().tolist()
            require(full[:len(prompt["input_ids"])] == prompt["input_ids"], "Prefixo de geração inesperado.")
            generated = full[len(prompt["input_ids"]):]
            del result
    finally:
        # PEFT can re-enable requires_grad when leaving disable_adapter().
        model.requires_grad_(False)
        model.eval()
        del batch
    require(model.get_model_status().enabled is True and model.get_model_status().merged_adapters == [],
            "Estado dos adaptadores não foi restaurado.")
    require(not any(parameter.requires_grad for parameter in model.parameters()), "Inferência deixou parâmetros treináveis.")
    return generated


def csv_bytes(predictions: list[dict]) -> bytes:
    columns = ("id_familia_docdb", "variante", "alvo_cpc_proxy", "codigo_normalizado", "texto_avaliado",
               "acerto_exato", "formato_sintatico_valido", "terminou_em_eos", "atingiu_limite")
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    for row in predictions:
        result = {}
        for key in columns:
            value = row.get(key)
            if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
                value = "'" + value
            result[key] = value
        writer.writerow(result)
    return buffer.getvalue().encode("utf-8-sig")


class Reporter:
    def __init__(self, root: Path, mirror: str | None):
        self.root = root
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        self.relative = RESULTS + "/avaliacao_cpc_" + stamp
        self.directory = training.safe_path(root, self.relative)
        self.directory.mkdir(parents=True, exist_ok=False)
        self.path = self.directory / "relatorio.json"
        self.mirror = training.safe_path(root, mirror) if mirror else None
        if self.mirror:
            require(self.mirror.is_relative_to(training.safe_path(root, RESULTS)) and self.mirror.suffix == ".json"
                    and not self.mirror.exists(), "Use um novo relatório JSON dentro da pasta de resultados.")
        self.data = {"estado": "avaliacao_cpc_iniciada", "etapa": "integridade", "erro": None,
                     "pasta_execucao": self.relative, "relatorio": self.path.relative_to(root).as_posix(),
                     "familias": 20, "geracoes_concluidas": 0, "metricas": None, "comparacao_pareada": None,
                     "teste_executado": False, "treinamento_executado": False,
                     "iniciado_em_utc": datetime.now(timezone.utc).isoformat(), "memoria": {},
                     "limite": "Diagnóstico em validação já usada para escolher época; não representa teste independente ou qualidade de extração."}
        self.save()

    def save(self):
        training.atomic_json(self.path, self.data)
        if self.mirror:
            training.atomic_json(self.mirror, self.data)

    def phase(self, value: str):
        self.data["etapa"] = value
        self.save()
        print("Avaliação CPC: " + value, flush=True)


def run(root: Path, profile_relative: str, mirror: str | None = None) -> tuple[int, Path]:
    root = root.resolve()
    reporter = Reporter(root, mirror)
    started = time.perf_counter()
    torch = None
    code = 1
    try:
        profile_bytes = training.safe_path(root, profile_relative).read_bytes()
        profile = json.loads(profile_bytes)
        material = preflight(root, profile)
        reporter.data.update(perfil=profile, sha256_perfil=sha256(profile_bytes),
            sha256_script=sha256(Path(__file__).read_bytes()), origem=material["provenance"],
            checkpoint=profile["checkpoint"]["diretorio"], familias_por_variante=20)
        reporter.phase("ambiente")
        versions = {name: metadata.version(name) for name in training.PACKAGES}
        for name, expected in helper.EXPECTED_PACKAGES.items():
            require(versions[name] == expected, f"Instale {name}=={expected}.")
        import torch as torch_module
        torch = torch_module
        require(torch.cuda.is_available() and torch.cuda.get_device_capability(0)[0] >= 6, "Selecione GPU com suporte NF4.")
        torch.cuda.set_device(0)
        torch.manual_seed(profile["semente"])
        torch.cuda.manual_seed_all(profile["semente"])
        random.seed(profile["semente"])
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cudnn.benchmark = False
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats(0)
        reporter.data.update(ambiente={"python": sys.version, "pacotes": versions},
            gpu={"nome": torch.cuda.get_device_name(0), "cuda_pytorch": torch.version.cuda,
                 "capacidade_cuda": list(torch.cuda.get_device_capability(0))})
        reporter.data["memoria"]["inicial"] = helper.memory_snapshot(torch)
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        from peft import PeftModel, prepare_model_for_kbit_training
        import bitsandbytes as bnb
        cache = Path(os.environ.get("HF_HOME", "/content/hf_cache_llm_eidt_br")) / "hub"
        cache.mkdir(parents=True, exist_ok=True)
        reporter.phase("tokenizacao_sem_alvos")
        tokenizer = AutoTokenizer.from_pretrained(profile["modelo"]["id"], revision=profile["modelo"]["revisao"],
            cache_dir=str(cache), trust_remote_code=False)
        require(tokenizer.eos_token_id is not None, "Tokenizador sem EOS.")
        prompts = [(row, build_prompt(tokenizer, row["entrada"])) for row in material["records"]]
        prompt_path = reporter.directory / "prompts_auditados.json"
        training.atomic_json(prompt_path, {"registros": [{"id_familia_docdb": row["id_familia_docdb"],
            "prompt": prompt["texto"], "sha256_prompt": prompt["sha256_prompt"], "tokens": prompt["tokens"]}
            for row, prompt in prompts], "alvo_no_prompt": False, "recortados": 0,
            "template_sha256": sha256(str(tokenizer.chat_template).encode("utf-8"))})
        reporter.data["tokenizacao"] = {"familias": 20, "max_tokens_prompt": max(item[1]["tokens"] for item in prompts),
            "recortadas": 0, "arquivo": prompt_path.relative_to(root).as_posix(), "sha256": sha256(prompt_path.read_bytes())}
        reporter.phase("carregamento_base_e_adaptador")
        quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
                                  bnb_4bit_compute_dtype=torch.float16)
        base = AutoModelForCausalLM.from_pretrained(profile["modelo"]["id"], revision=profile["modelo"]["revisao"],
            cache_dir=str(cache), trust_remote_code=False, low_cpu_mem_usage=True, quantization_config=quant,
            torch_dtype=torch.float16, device_map={"": 0}, attn_implementation="sdpa")
        require(getattr(base, "is_loaded_in_4bit", False) and any(isinstance(m, bnb.nn.Linear4bit) for m in base.modules()),
                "Modelo não foi carregado em quatro bits.")
        base = prepare_model_for_kbit_training(base, use_gradient_checkpointing=False)
        model = PeftModel.from_pretrained(base, str(material["checkpoint_directory"] / "adapter"),
                                         is_trainable=False, autocast_adapter_dtype=True)
        model.requires_grad_(False)
        model.eval()
        model.config.use_cache = True
        require(all(parameter.device.type == "cuda" for parameter in model.parameters()), "Offload não faz parte deste perfil.")
        require(model.get_model_status().enabled is True and model.get_model_status().merged_adapters == [],
                "Adaptadores indisponíveis ou já mesclados.")
        reporter.data["memoria"]["apos_carregamento"] = helper.memory_snapshot(torch)
        predictions = []
        prediction_path = reporter.directory / "predicoes_cpc.jsonl"
        reporter.data["arquivo_predicoes"] = prediction_path.relative_to(root).as_posix()
        with prediction_path.open("xb") as stream:
            for variant in ("base", "adaptado"):
                reporter.phase("geracao_" + variant)
                for row, prompt in prompts:
                    generated = generate_one(torch, model, tokenizer, prompt, variant, amp_dtype=torch.float16)
                    result = score_prediction(tokenizer, generated, row["alvo_cpc_proxy"])
                    result.update(id_familia_docdb=row["id_familia_docdb"], variante=variant, particao="validacao",
                                  sha256_prompt=prompt["sha256_prompt"], tokens_prompt=prompt["tokens"])
                    stream.write((json.dumps(result, ensure_ascii=False) + "\n").encode("utf-8"))
                    stream.flush()
                    os.fsync(stream.fileno())
                    predictions.append(result)
                    reporter.data["geracoes_concluidas"] = len(predictions)
                    reporter.save()
                    print(json.dumps({"variante": variant, "familia": row["id_familia_docdb"],
                                      "concluidas": len(predictions), "total": 40}, ensure_ascii=False), flush=True)
        metrics, paired = summarize(predictions, [row["id_familia_docdb"] for row in material["records"]])
        csv_path = reporter.directory / "comparacao_cpc.csv"
        csv_path.write_bytes(csv_bytes(predictions))
        reporter.data.update(metricas=metrics, comparacao_pareada=paired,
            arquivo_csv=csv_path.relative_to(root).as_posix(),
            sha256_arquivos={prediction_path.name: sha256(prediction_path.read_bytes()), csv_path.name: sha256(csv_path.read_bytes())},
            estado="avaliacao_cpc_concluida", etapa="concluido")
        code = 0
    except (Exception, KeyboardInterrupt) as error:
        oom = torch is not None and isinstance(error, torch.cuda.OutOfMemoryError)
        reporter.data.update(estado="memoria_gpu_insuficiente" if oom else "avaliacao_cpc_interrompida" if isinstance(error, KeyboardInterrupt) else "avaliacao_cpc_falhou",
            etapa_falha=reporter.data["etapa"], erro={"tipo": type(error).__name__, "mensagem": helper.safe_error_message(error)})
    finally:
        if torch is not None and torch.cuda.is_available():
            try:
                snapshot = helper.memory_snapshot(torch)
                reporter.data["memoria"]["final"] = snapshot
                reporter.data.update(pico_alocado_gib=snapshot["pico_alocado_gib"], pico_reservado_gib=snapshot["pico_reservado_gib"])
            except Exception:
                pass
        reporter.data.update(duracao_segundos=round(time.perf_counter() - started, 3),
                             finalizado_em_utc=datetime.now(timezone.utc).isoformat())
        reporter.save()
        fields = ("estado", "familias", "geracoes_concluidas", "metricas", "comparacao_pareada", "checkpoint",
                  "pico_alocado_gib", "pico_reservado_gib", "duracao_segundos", "arquivo_predicoes", "arquivo_csv", "erro")
        print("RESUMO DA AVALIAÇÃO — copie este bloco", flush=True)
        print(json.dumps({key: reporter.data.get(key) for key in fields}, ensure_ascii=False, indent=2), flush=True)
        print("Relatório completo: " + str(reporter.path), flush=True)
    return code, reporter.path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz", type=Path, required=True)
    parser.add_argument("--perfil", default="config/perfil_avaliacao_cpc_validacao.json")
    parser.add_argument("--saida_relatorio")
    parser.add_argument("--validar_apenas", action="store_true")
    args = parser.parse_args()
    if args.validar_apenas:
        root = args.raiz.resolve()
        profile = json.loads(training.safe_path(root, args.perfil).read_bytes())
        material = preflight(root, profile)
        print(json.dumps({"estado": "integridade_avaliacao_aprovada", "familias": len(material["records"]),
            "checkpoint": profile["checkpoint"]["diretorio"], "perfil": profile["id"], "proveniencia": material["provenance"]}, ensure_ascii=False))
        return
    code, _ = run(args.raiz, args.perfil, args.saida_relatorio)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
