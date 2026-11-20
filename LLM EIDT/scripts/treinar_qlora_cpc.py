"""Treino QLoRA CPC exploratório; 160 famílias, 20 de validação, teste reservado.

Executa três épocas com perda CPC+EOS ponderada por tokens, validação a cada
época e retomada somente a partir de checkpoints integralmente verificados.
Importável sem PyTorch para testar integridade e protocolo em CPU.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from datetime import datetime, timezone
from importlib import metadata
import json
import math
import os
from pathlib import Path
import random
import re
import sys
import time
import uuid

import testar_qlora_gpu as helper


PROFILE_ID = "br_patstat_200_qwen3_8b_qlora_nf4_fp16_train_v1"
CAPACITY_ID = "br_patstat_200_qwen3_8b_qlora_nf4_fp16_smoke_v2_ctx1024"
RESULTS = "resultados/etapa_2/piloto_br_200"
PACKAGES = ("torch", "transformers", "peft", "bitsandbytes", "accelerate",
            "huggingface-hub", "tokenizers", "safetensors", "jinja2")
require = helper.require
sha256 = helper.sha256


def safe_path(root: Path, relative: str) -> Path:
    require(isinstance(relative, str) and bool(relative.strip()), "Caminho relativo vazio.")
    path = Path(relative)
    require(not path.is_absolute() and ".." not in path.parts, "Use um caminho relativo dentro do projeto.")
    target = (root / path).resolve()
    require(target.is_relative_to(root.resolve()), "Caminho escapou do projeto.")
    return target


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name("." + path.name + "." + uuid.uuid4().hex + ".tmp")
    with temporary.open("xb") as stream:
        stream.write(helper.json_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def checked(root: Path, origin: dict, key: str) -> bytes:
    data = safe_path(root, origin[key]).read_bytes()
    require(sha256(data) == origin["sha256_" + key], f"SHA-256 divergente: {origin[key]}.")
    return data


def validate_inputs(root: Path, profile: dict, diagnostic_relative: str) -> tuple[list, list, dict]:
    require(profile["id"] == PROFILE_ID, "Perfil de treinamento desconhecido.")
    require(profile["resultados"] == RESULTS, "Pasta de resultados fora do protocolo.")
    require(profile["treino"] == {"max_length": 1024, "microbatch": 1, "acumulacao": 16,
                                  "epocas": 3, "checkpoint_cada_passos": 5}, "Treino difere do perfil auditado.")
    require(profile["otimizador"] == {"learning_rate": 0.0003, "weight_decay": 0.01,
         "max_grad_norm": 1.0, "scheduler": "constant", "warmup_steps": 0}, "Otimizador difere do perfil auditado.")
    require(profile["semente"] == 42, "Semente diferente do protocolo.")
    origin = profile["origem"]
    helper_bytes = checked(root, origin, "helper")
    require(sha256(Path(helper.__file__).read_bytes()) == sha256(helper_bytes),
            "O helper importado difere do helper congelado.")
    capacity = json.loads(checked(root, origin, "perfil_capacidade"))
    require(capacity["id"] == CAPACITY_ID, "Use o diagnóstico aprovado de contexto 1024.")
    for key in ("config", "auditoria_preprocessamento", "treino"):
        require(origin[key] == capacity["origem"][key]
                and origin["sha256_" + key] == capacity["origem"]["sha256_" + key],
                f"Origem {key} difere do diagnóstico de capacidade.")
    for key in ("modelo", "quantizacao", "lora", "semente"):
        require(profile[key] == capacity[key], f"{key} difere do teste de capacidade aprovado.")
    _, train = helper.validate_inputs(root, capacity)
    audit = json.loads(checked(root, origin, "auditoria_preprocessamento"))
    valid_bytes = checked(root, origin, "validacao")
    require(audit["sha256_arquivos"]["validacao_cpc.jsonl"] == origin["sha256_validacao"],
            "Validação diverge da auditoria de pré-processamento.")
    valid = [json.loads(line) for line in valid_bytes.decode("utf-8").splitlines() if line.strip()]
    require(len(valid) == 20, "Esperadas 20 famílias de validação.")
    identifiers = {row["id_familia_docdb"] for row in train}
    for row in valid:
        family = row["id_familia_docdb"]
        require(isinstance(family, str) and family.isdigit() and int(family) > 0
                and family not in identifiers, "Família de validação duplicada ou sobreposta ao treino.")
        identifiers.add(family)
        require(row["particao"] == "validacao", "Arquivo contém outra partição.")
        require(isinstance(row["alvo_cpc_proxy"], str) and bool(row["alvo_cpc_proxy"].strip()), "CPC vazio.")
        for field in ("titulo", "resumo"):
            require(row["entrada"]["idiomas"][field] in {"pt", "en"}, "Idioma fora de pt/en.")
            require(bool(row["entrada"]["textos"][field].strip()), "Texto vazio na validação.")
    diagnostic_bytes = safe_path(root, diagnostic_relative).read_bytes()
    diagnostic = json.loads(diagnostic_bytes)
    require(diagnostic["estado"] == "teste_qlora_aprovado" and diagnostic["etapa"] == "concluido",
            "É necessário um diagnóstico QLoRA aprovado.")
    require(not diagnostic.get("erro") and not diagnostic.get("etapa_falha"),
            "Diagnóstico marcado como aprovado ainda contém uma falha.")
    require(diagnostic["sha256_perfil"] == origin["sha256_perfil_capacidade"]
            and diagnostic["perfil"] == capacity, "Diagnóstico aprovado pertence a outro perfil.")
    step = diagnostic["passo_executado"]
    require(step["passos_otimizador"] == 1 and step["tensores_lora_alterados"] > 0
            and math.isfinite(step["loss"]) and step["grad_scaler_depois"] >= step["grad_scaler_antes"],
            "Diagnóstico não confirma uma atualização finita dos adaptadores.")
    require(diagnostic["tokenizacao"]["contexto"] == 1024
            and diagnostic["tokenizacao"]["revisao_necessaria"] == 0, "Tokenização do diagnóstico exige revisão.")
    labels = {row["alvo_cpc_proxy"] for row in train}
    provenance = {"diagnostico": diagnostic_relative, "sha256_diagnostico": sha256(diagnostic_bytes),
                  "familias_treino": len(train), "familias_validacao": len(valid),
                  "cpc_distintos_treino": len(labels),
                  "validacao_cpc_ausente_treino": sum(row["alvo_cpc_proxy"] not in labels for row in valid),
                  "teste": "Partição reservada: nenhum arquivo de teste foi aberto.",
                  "limite": "CPC proxy é o primeiro símbolo integral em ordem alfabética; não é anotação de extração."}
    return train, valid, provenance


def target_count(example: dict) -> int:
    """Causal LM predicts labels[1:]; a label at position zero is never a target."""
    count = sum(label != -100 for label in example["labels"][1:])
    require(count > 0, "Exemplo sem tokens supervisionados após o deslocamento causal.")
    return count


def epoch_groups(size: int, accumulation: int, seed: int, epoch: int) -> list[list[int]]:
    require(size > 0 and accumulation > 0 and epoch >= 1, "Dimensões de época inválidas.")
    indices = list(range(size))
    random.Random(seed + epoch).shuffle(indices)
    return [indices[start:start + accumulation] for start in range(0, size, accumulation)]


def tensor_batch(torch, example: dict, device: str) -> dict:
    # Microbatch 1: tensor at the actual sequence length, never fixed 1024 padding.
    return {key: torch.tensor([example[key]], dtype=torch.long, device=device)
            for key in ("input_ids", "attention_mask", "labels")}


def amp_context(torch, device: str, dtype):
    return torch.autocast(device_type=device.split(":")[0], dtype=dtype) if dtype is not None else nullcontext()


def train_group(torch, model, optimizer, scaler, examples: list[dict], parameters: list,
                max_grad_norm: float, device: str = "cuda:0", amp_dtype=None) -> dict:
    """One optimizer update; backward frees each microbatch graph immediately."""
    counts = [target_count(example) for example in examples]
    total = sum(counts)
    optimizer.zero_grad(set_to_none=True)
    loss_sum = 0.0
    for example, count in zip(examples, counts):
        batch = tensor_batch(torch, example, device)
        with amp_context(torch, device, amp_dtype):
            output = model(**batch, use_cache=False)
            loss = output.loss
            require(bool(torch.isfinite(loss).item()), "Perda não finita; atualização interrompida.")
            loss_sum += float(loss.detach().cpu()) * count
            weighted = loss * (count / total)
        scaler.scale(weighted).backward()
        del output, loss, weighted, batch
    scaler.unscale_(optimizer)
    gradients = [parameter.grad for parameter in parameters if parameter.grad is not None]
    require(gradients and all(bool(torch.isfinite(grad).all().item()) for grad in gradients),
            "Gradientes ausentes ou não finitos; nenhum passo será contabilizado.")
    require(any(bool(torch.count_nonzero(grad).item()) for grad in gradients), "Todos os gradientes são zero.")
    norm = torch.nn.utils.clip_grad_norm_(parameters, max_grad_norm)
    require(bool(torch.isfinite(norm).item()), "Norma de gradiente não finita.")
    scale_before = scaler.get_scale()
    scaler.step(optimizer)
    scaler.update()
    require(scaler.get_scale() >= scale_before, "GradScaler ignorou a atualização por overflow.")
    require(all(bool(torch.isfinite(parameter).all().item()) for parameter in parameters),
            "Parâmetro LoRA não finito após a atualização.")
    optimizer.zero_grad(set_to_none=True)
    return {"loss_soma_tokens": loss_sum, "tokens": total, "loss": loss_sum / total,
            "familias": len(examples), "norma_gradiente_antes_clip": float(norm.detach().cpu()),
            "grad_scaler": scaler.get_scale()}


def evaluate(torch, model, examples: list[dict], device: str = "cuda:0", amp_dtype=None) -> dict:
    previous = model.training
    model.eval()
    loss_sum, total = 0.0, 0
    try:
        with torch.no_grad():
            for example in examples:
                count = target_count(example)
                batch = tensor_batch(torch, example, device)
                with amp_context(torch, device, amp_dtype):
                    output = model(**batch, use_cache=False)
                    loss = output.loss
                require(bool(torch.isfinite(loss).item()), "Perda de validação não finita.")
                loss_sum += float(loss.detach().cpu()) * count
                total += count
                del output, loss, batch
    finally:
        model.train(previous)
    require(total > 0, "Validação sem tokens.")
    return {"loss": loss_sum / total, "tokens": total, "familias": len(examples)}


def new_progress() -> dict:
    return {"global_step": 0, "next_epoch": 1, "next_group": 0,
            "epoch_loss_sum": 0.0, "epoch_tokens": 0, "baseline": None,
            "epocas": [], "melhor": None}


def update_best(progress: dict, epoch: int, loss: float, checkpoint_relative: str) -> None:
    require(epoch in {1, 2, 3} and math.isfinite(loss), "Candidato de validação inválido.")
    best = progress["melhor"]
    if best is None or loss < best["loss"]:
        progress["melhor"] = {"epoca": epoch, "loss": loss, "checkpoint": checkpoint_relative}


def validate_progress(progress: dict) -> None:
    epoch, group, step = progress["next_epoch"], progress["next_group"], progress["global_step"]
    require(type(epoch) is int and type(group) is int and type(step) is int
            and 1 <= epoch <= 4 and 0 <= group < 10 and (epoch != 4 or group == 0), "Cursor inválido.")
    require(step == (epoch - 1) * 10 + group and 0 < step <= 30 and step % 5 == 0,
            "Checkpoint não corresponde a um limite de cinco atualizações.")
    require(len(progress["epocas"]) == epoch - 1
            and [item["epoca"] for item in progress["epocas"]] == list(range(1, epoch)),
            "Checkpoint pula uma validação de fim de época.")
    require(progress["baseline"] is not None and math.isfinite(progress["baseline"]["loss"]),
            "Checkpoint sem validação inicial finita.")
    if group == 0:
        require(progress["epoch_tokens"] == 0 and progress["epoch_loss_sum"] == 0,
                "Acumulador de época não foi reiniciado.")
    else:
        require(progress["epoch_tokens"] > 0 and math.isfinite(progress["epoch_loss_sum"]),
                "Acumulador parcial de época ausente.")
    for item in progress["epocas"]:
        require(math.isfinite(item["validacao"]["loss"]) and math.isfinite(item["treino_loss"]),
                "Histórico contém perda não finita.")
    if progress["epocas"]:
        best = min(progress["epocas"], key=lambda item: (item["validacao"]["loss"], item["epoca"]))
        require(progress["melhor"] == {"epoca": best["epoca"], "loss": best["validacao"]["loss"],
                                        "checkpoint": best["checkpoint"]}, "Seleção de melhor época inconsistente.")
    else:
        require(progress["melhor"] is None, "Baseline não pode concorrer à seleção.")


def verify_checkpoint(root: Path, relative: str, fingerprint: dict | None = None) -> tuple[Path, dict]:
    """Validate every byte and the complete file inventory before any torch.load."""
    directory = safe_path(root, relative)
    require(directory.is_dir() and not directory.is_symlink(), "Checkpoint inexistente.")
    manifest_path = directory / "manifest.json"
    require(manifest_path.is_file(), "Checkpoint incompleto: falta manifesto de commit.")
    manifest = json.loads(manifest_path.read_bytes())
    require(manifest.get("formato") == "qlora-cpc-checkpoint-1", "Formato de checkpoint desconhecido.")
    files = manifest["arquivos"]
    require(isinstance(files, dict) and {"progresso.json", "trainer_state.pt", "adapter/adapter_config.json",
                "adapter/adapter_model.safetensors"}.issubset(files), "Checkpoint sem arquivos essenciais.")
    actual = set()
    for item in directory.rglob("*"):
        require(not item.is_symlink(), "Links simbólicos não são aceitos no checkpoint.")
        if item.is_file() and item != manifest_path:
            actual.add(item.relative_to(directory).as_posix())
    require(actual == set(files), "Inventário do checkpoint diverge do manifesto.")
    for name, expected in files.items():
        require(name != "manifest.json" and bool(re.fullmatch(r"[0-9a-f]{64}", expected)), "Entrada inválida no manifesto.")
        data = safe_path(directory, name).read_bytes()
        require(sha256(data) == expected, f"Checkpoint corrompido: {name}.")
    envelope = json.loads((directory / "progresso.json").read_bytes())
    if fingerprint is not None:
        require(envelope["compatibilidade"] == fingerprint,
                "Retomada incompatível: código, configuração, dados, diagnóstico ou ambiente mudaram.")
    validate_progress(envelope["progresso"])
    return directory, envelope


def save_checkpoint(torch, model, tokenizer, optimizer, scaler, root: Path, relative: str,
                    fingerprint: dict, progress: dict) -> None:
    validate_progress(progress)
    directory = safe_path(root, relative)
    directory.mkdir(parents=True, exist_ok=False)
    adapter = directory / "adapter"
    model.save_pretrained(str(adapter), safe_serialization=True, save_embedding_layers=False)
    tokenizer.save_pretrained(str(adapter))
    state = {"global_step": progress["global_step"], "optimizer": optimizer.state_dict(),
             "scaler": scaler.state_dict(), "torch_rng": torch.get_rng_state(),
             "cuda_rng": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
             "python_rng": random.getstate()}
    torch.save(state, directory / "trainer_state.pt")
    atomic_json(directory / "progresso.json", {"compatibilidade": fingerprint, "progresso": progress})
    files = {item.relative_to(directory).as_posix(): sha256(item.read_bytes())
             for item in sorted(directory.rglob("*")) if item.is_file()}
    # This last atomic rename is the commit marker. Interrupted folders are never resumable.
    atomic_json(directory / "manifest.json", {"formato": "qlora-cpc-checkpoint-1", "arquivos": files})
    verify_checkpoint(root, relative, fingerprint)


def restore_state(torch, optimizer, scaler, directory: Path, progress: dict) -> None:
    # Caller must verify_checkpoint immediately before this; only own tensor/primitive state.
    state = torch.load(directory / "trainer_state.pt", map_location="cpu", weights_only=True)
    require(state["global_step"] == progress["global_step"], "Estado do otimizador diverge do cursor.")
    optimizer.load_state_dict(state["optimizer"])
    scaler.load_state_dict(state["scaler"])
    torch.set_rng_state(state["torch_rng"])
    if state["cuda_rng"]:
        require(torch.cuda.is_available() and len(state["cuda_rng"]) == torch.cuda.device_count(),
                "Quantidade de GPUs incompatível com RNG salvo.")
        torch.cuda.set_rng_state_all(state["cuda_rng"])
    random.setstate(state["python_rng"])


class Reporter:
    def __init__(self, root: Path, mirror: str | None):
        self.root = root
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        self.relative = RESULTS + "/treino_qlora_" + stamp
        self.directory = safe_path(root, self.relative)
        self.directory.mkdir(parents=True, exist_ok=False)
        self.path = self.directory / "relatorio.json"
        self.mirror = safe_path(root, mirror) if mirror else None
        if self.mirror:
            require(self.mirror.is_relative_to(safe_path(root, RESULTS)) and self.mirror.suffix == ".json",
                    "O relatório de chamada deve ser JSON dentro de resultados/etapa_2/piloto_br_200.")
            require(not self.mirror.exists(), "Relatório de chamada já existe; use um nome novo.")
        self.data = {"estado": "treino_qlora_iniciado", "etapa": "integridade", "erro": None,
                     "iniciado_em_utc": datetime.now(timezone.utc).isoformat(),
                     "pasta_execucao": self.relative, "relatorio": self.path.relative_to(root).as_posix(),
                     "passos_concluidos": 0, "epocas_concluidas": 0, "adaptador_selecionado": None,
                     "ultimo_checkpoint": None, "memoria": {}, "teste_executado": False,
                     "limite": "Treino do CPC proxy; conclusão não demonstra qualidade de extração ou generalização."}
        self.save()

    def save(self):
        atomic_json(self.path, self.data)
        if self.mirror:
            atomic_json(self.mirror, self.data)

    def phase(self, name: str):
        self.data["etapa"] = name
        self.save()
        print("Treino QLoRA: " + name, flush=True)

    def progress(self, progress: dict):
        best = progress["melhor"] or {}
        self.data.update(passos_concluidos=progress["global_step"], epocas_concluidas=len(progress["epocas"]),
                         melhor_epoca=best.get("epoca"), melhor_validacao_loss=best.get("loss"),
                         validacao_baseline_loss=(progress["baseline"] or {}).get("loss"),
                         historico_epocas=progress["epocas"], progresso=progress)
        self.save()


def run(root: Path, profile_relative: str, diagnostic_relative: str, resume: str | None = None,
        report_relative: str | None = None) -> tuple[int, Path]:
    root = root.resolve()
    reporter = Reporter(root, report_relative)
    started = time.perf_counter()
    torch = model = optimizer = scaler = None
    code = 1
    try:
        profile_bytes = safe_path(root, profile_relative).read_bytes()
        profile = json.loads(profile_bytes)
        train_records, val_records, provenance = validate_inputs(root, profile, diagnostic_relative)
        reporter.data.update(perfil=profile, sha256_perfil=sha256(profile_bytes), origem=provenance,
                             retomada_de=resume, scheduler="constant", warmup_steps=0,
                             perda="Média por token CPC+EOS; treino da época agrega previsões antes de cada atualização.")
        reporter.phase("ambiente")
        versions = {package: metadata.version(package) for package in PACKAGES}
        for package, expected in helper.EXPECTED_PACKAGES.items():
            require(versions[package] == expected, f"Instale {package}=={expected}; versão atual {versions[package]}.")
        import torch as torch_module
        torch = torch_module
        require(torch.cuda.is_available(), "Selecione GPU no Colab.")
        require(torch.cuda.get_device_capability(0)[0] >= 6, "GPU sem suporte NF4 requerido.")
        torch.cuda.set_device(0)
        torch.manual_seed(profile["semente"])
        torch.cuda.manual_seed_all(profile["semente"])
        random.seed(profile["semente"])
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cudnn.benchmark = False
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats(0)
        gpu = {"nome": torch.cuda.get_device_name(0), "capacidade_cuda": list(torch.cuda.get_device_capability(0)),
               "cuda_pytorch": torch.version.cuda, "quantidade": torch.cuda.device_count()}
        fingerprint = {"sha256_script": sha256(Path(__file__).read_bytes()),
                       "sha256_perfil": sha256(profile_bytes), "origem": profile["origem"],
                       "sha256_diagnostico": provenance["sha256_diagnostico"], "pacotes": versions,
                       "python": list(sys.version_info[:2]), "gpu": gpu}
        reporter.data.update(ambiente={"pacotes": versions, "python": sys.version}, gpu=gpu,
                             compatibilidade=fingerprint,
                             reprodutibilidade="Ordem e RNG preservados; não se promete igualdade bit a bit entre kernels CUDA.")
        reporter.data["memoria"]["inicial"] = helper.memory_snapshot(torch)
        progress, resume_directory = new_progress(), None
        if resume:
            resume_directory, envelope = verify_checkpoint(root, resume, fingerprint)
            progress = envelope["progresso"]
            reporter.data["ultimo_checkpoint"] = resume
            if progress["melhor"]:
                verify_checkpoint(root, progress["melhor"]["checkpoint"], fingerprint)
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training, PeftModel
        import bitsandbytes as bnb
        cache = Path(os.environ.get("HF_HOME", "/content/hf_cache_llm_eidt_br")) / "hub"
        cache.mkdir(parents=True, exist_ok=True)
        reporter.phase("tokenizacao_treino_validacao")
        tokenizer = AutoTokenizer.from_pretrained(profile["modelo"]["id"], revision=profile["modelo"]["revisao"],
                                                   cache_dir=str(cache), trust_remote_code=False)
        prepared, evidence = {}, []
        for partition, records in (("treino", train_records), ("validacao", val_records)):
            prepared[partition] = []
            for record in records:
                example, info = helper.prepare_example(tokenizer, record, profile["treino"]["max_length"])
                info["particao"] = partition
                info["tokens_supervisionados_apos_shift"] = target_count(example)
                prepared[partition].append(example)
                evidence.append(info)
        token_path = reporter.directory / "tokenizacao_treino_validacao.json"
        atomic_json(token_path, {"contexto_maximo": 1024, "padding_fixo": False, "registros": evidence,
                               "template_sha256": sha256(str(tokenizer.chat_template).encode("utf-8"))})
        reporter.data["tokenizacao"] = {"arquivo": token_path.relative_to(root).as_posix(),
             "sha256": sha256(token_path.read_bytes()), "recortadas": sum(item["recortado"] for item in evidence),
             "max_tokens": max(item["tokens_apos_recorte"] for item in evidence), "familias": len(evidence)}
        reporter.phase("carregamento_nf4")
        quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                  bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16)
        model = AutoModelForCausalLM.from_pretrained(profile["modelo"]["id"], revision=profile["modelo"]["revisao"],
            cache_dir=str(cache), trust_remote_code=False, low_cpu_mem_usage=True, quantization_config=quant,
            torch_dtype=torch.float16, device_map={"": 0}, attn_implementation="sdpa")
        require(getattr(model, "is_loaded_in_4bit", False)
                and any(isinstance(module, bnb.nn.Linear4bit) for module in model.modules()), "Carregamento não usa NF4.")
        require(all(parameter.device.type == "cuda" for parameter in model.parameters()), "Offload não faz parte do perfil.")
        model.config.use_cache = False
        model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True,
                                               gradient_checkpointing_kwargs={"use_reentrant": False})
        if resume_directory:
            verify_checkpoint(root, resume, fingerprint)
            model = PeftModel.from_pretrained(model, str(resume_directory / "adapter"),
                                             is_trainable=True, autocast_adapter_dtype=True)
        else:
            options = profile["lora"]
            model = get_peft_model(model, LoraConfig(r=options["r"], lora_alpha=options["alpha"],
                lora_dropout=options["dropout"], target_modules=options["target_modules"], bias="none",
                task_type=TaskType.CAUSAL_LM), autocast_adapter_dtype=True)
        named = [(name, parameter) for name, parameter in model.named_parameters() if parameter.requires_grad]
        require(named and all("lora_" in name for name, _ in named), "Parâmetros treináveis fora de LoRA.")
        for _, parameter in named:
            if parameter.dtype != torch.float32:
                parameter.data = parameter.data.to(torch.float32)
        require(all(parameter.device.type == "cuda" for parameter in model.parameters()), "Peso fora da GPU após PEFT.")
        parameters = [parameter for _, parameter in named]
        reporter.data["lora"] = {"parametros_treinaveis": sum(parameter.numel() for parameter in parameters),
                                 "dtype_treinavel": "float32", "dtype_calculo": "float16"}
        optimizer = torch.optim.AdamW(parameters, lr=profile["otimizador"]["learning_rate"],
                                     weight_decay=profile["otimizador"]["weight_decay"])
        scaler = torch.amp.GradScaler("cuda", init_scale=128.0)
        if resume_directory:
            # Loading the model, adapters and optimizer must precede restoring dropout RNG.
            verify_checkpoint(root, resume, fingerprint)
            restore_state(torch, optimizer, scaler, resume_directory, progress)
        model.train()
        reporter.data["memoria"]["apos_preparacao"] = helper.memory_snapshot(torch)
        if progress["baseline"] is None:
            reporter.phase("validacao_inicial_referencia")
            progress["baseline"] = evaluate(torch, model, prepared["validacao"], amp_dtype=torch.float16)
        reporter.progress(progress)
        while progress["next_epoch"] <= profile["treino"]["epocas"]:
            epoch = progress["next_epoch"]
            groups = epoch_groups(len(prepared["treino"]), 16, profile["semente"], epoch)
            for group_index in range(progress["next_group"], len(groups)):
                reporter.phase(f"treino_epoca_{epoch}_grupo_{group_index + 1}")
                metrics = train_group(torch, model, optimizer, scaler,
                    [prepared["treino"][index] for index in groups[group_index]], parameters,
                    profile["otimizador"]["max_grad_norm"], amp_dtype=torch.float16)
                progress["global_step"] += 1
                progress["epoch_loss_sum"] += metrics["loss_soma_tokens"]
                progress["epoch_tokens"] += metrics["tokens"]
                progress["next_group"] = group_index + 1
                reporter.data["ultima_atualizacao"] = metrics
                checkpoint = reporter.relative + f"/checkpoints/passo_{progress['global_step']:06d}"
                if group_index + 1 == len(groups):
                    reporter.phase(f"validacao_epoca_{epoch}")
                    validation = evaluate(torch, model, prepared["validacao"], amp_dtype=torch.float16)
                    progress["epocas"].append({"epoca": epoch,
                         "treino_loss": progress["epoch_loss_sum"] / progress["epoch_tokens"],
                         "treino_tokens": progress["epoch_tokens"], "validacao": validation, "checkpoint": checkpoint})
                    update_best(progress, epoch, validation["loss"], checkpoint)
                    progress.update(next_epoch=epoch + 1, next_group=0, epoch_loss_sum=0.0, epoch_tokens=0)
                reporter.data["memoria"]["ultimo_passo"] = helper.memory_snapshot(torch)
                reporter.progress(progress)
                if progress["global_step"] % profile["treino"]["checkpoint_cada_passos"] == 0:
                    reporter.phase("salvando_checkpoint")
                    save_checkpoint(torch, model, tokenizer, optimizer, scaler, root, checkpoint, fingerprint, progress)
                    reporter.data["ultimo_checkpoint"] = checkpoint
                    reporter.save()
                print(json.dumps({"passo": progress["global_step"], "total": 30, "epoca": epoch,
                                  "loss_grupo": metrics["loss"], "checkpoint": reporter.data["ultimo_checkpoint"]},
                                  ensure_ascii=False), flush=True)
        require(progress["global_step"] == 30 and len(progress["epocas"]) == 3, "Treinamento incompleto.")
        best = progress["melhor"]
        _, best_envelope = verify_checkpoint(root, best["checkpoint"], fingerprint)
        require(any(item["epoca"] == best["epoca"] and item["validacao"]["loss"] == best["loss"]
                    for item in best_envelope["progresso"]["epocas"]), "Adaptador selecionado não corresponde à validação.")
        selected = {"epoca": best["epoca"], "validacao_loss": best["loss"],
                    "checkpoint": best["checkpoint"], "adaptador": best["checkpoint"] + "/adapter",
                    "criterio": "Menor perda por token na validação entre épocas 1–3; empate favorece a primeira.",
                    "sha256_manifest_checkpoint": sha256((safe_path(root, best["checkpoint"]) / "manifest.json").read_bytes()),
                    "teste_executado": False}
        atomic_json(reporter.directory / "adaptador_selecionado.json", selected)
        reporter.data.update(estado="treino_qlora_concluido", etapa="concluido",
                             adaptador_selecionado=selected["adaptador"], selecao=selected,
                             melhorou_sobre_baseline=best["loss"] < progress["baseline"]["loss"],
                             delta_validacao_baseline=best["loss"] - progress["baseline"]["loss"])
        code = 0
    except (Exception, KeyboardInterrupt) as error:
        oom = torch is not None and isinstance(error, torch.cuda.OutOfMemoryError)
        state = "memoria_gpu_insuficiente" if oom else "treino_qlora_falhou"
        if isinstance(error, KeyboardInterrupt):
            state = "treino_qlora_interrompido"
        reporter.data.update(estado=state, etapa_falha=reporter.data["etapa"],
                             erro={"tipo": type(error).__name__, "mensagem": helper.safe_error_message(error)})
    finally:
        if torch is not None and torch.cuda.is_available():
            try:
                memory = helper.memory_snapshot(torch)
                reporter.data["memoria"]["final"] = memory
                reporter.data.update(pico_alocado_gib=memory["pico_alocado_gib"],
                                     pico_reservado_gib=memory["pico_reservado_gib"])
            except Exception:
                pass
        reporter.data.update(duracao_segundos=round(time.perf_counter() - started, 3),
                             finalizado_em_utc=datetime.now(timezone.utc).isoformat())
        reporter.save()
        keys = ("estado", "passos_concluidos", "epocas_concluidas", "melhor_epoca", "melhor_validacao_loss",
                "validacao_baseline_loss", "adaptador_selecionado", "ultimo_checkpoint", "pico_alocado_gib",
                "pico_reservado_gib", "duracao_segundos", "erro", "pasta_execucao")
        print("RESUMO DO TREINAMENTO — copie este bloco", flush=True)
        print(json.dumps({key: reporter.data.get(key) for key in keys}, ensure_ascii=False, indent=2), flush=True)
        print("Relatório completo: " + str(reporter.path), flush=True)
    return code, reporter.path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz", type=Path, required=True)
    parser.add_argument("--perfil", default="config/perfil_treino_qlora_1024.json")
    parser.add_argument("--diagnostico", required=True)
    parser.add_argument("--retomar", help="Diretório relativo de checkpoint com manifest.json completo.")
    parser.add_argument("--saida_relatorio", help="JSON de chamada novo, relativo à pasta de resultados da etapa 2.")
    args = parser.parse_args()
    code, _ = run(args.raiz, args.perfil, args.diagnostico, args.retomar, args.saida_relatorio)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
