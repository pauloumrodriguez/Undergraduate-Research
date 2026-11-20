"""Teste final CPC do piloto, com procedimento de geração e pontuação do 06."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from importlib import metadata
import json, os, random, re, sys, time
from pathlib import Path
import avaliar_cpc_geracao as previous
import testar_qlora_gpu as helper
import treinar_qlora_cpc as training
PROFILE_ID = 'br_patstat_200_qwen3_8b_cpc_teste_v1'
RESULTS = 'resultados/etapa_4/piloto_br_200'
ORIGIN_KEYS = ('perfil_validacao','script_validacao','relatorio_validacao','auditoria_preprocessamento','teste')
require, sha256 = helper.require, helper.sha256
canonical_cpc = previous.canonical_cpc
build_prompt = previous.build_prompt
score_prediction = previous.score_prediction
generate_one = previous.generate_one
summarize = previous.summarize
csv_bytes = previous.csv_bytes


def preflight(root: Path, profile: dict) -> dict:
    require(profile['id'] == PROFILE_ID and profile['resultados'] == RESULTS, 'Perfil de teste desconhecido.')
    origin = profile['origem']
    # Congelar o procedimento e conferir o checkpoint antes de abrir o teste.
    old_profile = json.loads(training.checked(root, origin, 'perfil_validacao'))
    training.checked(root, origin, 'script_validacao')
    require(sha256(Path(previous.__file__).read_bytes()) == origin['sha256_script_validacao'], 'Programa 06 diferente do congelado.')
    for key in ('modelo', 'quantizacao', 'checkpoint', 'geracao', 'semente'):
        require(profile[key] == old_profile[key], 'Procedimento mudou após validação: ' + key)
    expected = dict(old_profile['avaliacao'], particao='teste')
    require(profile['avaliacao'] == expected, 'Métricas ou coorte de teste divergentes.')
    validation = json.loads(training.checked(root, origin, 'relatorio_validacao'))
    require(validation['estado'] == 'avaliacao_cpc_concluida' and not validation.get('erro')
            and validation['geracoes_concluidas'] == 40 and validation['teste_executado'] is False,
            'O diagnóstico 06 não confirma conclusão sem uso do teste.')
    require(validation['perfil'] == old_profile
            and validation['sha256_perfil'] == origin['sha256_perfil_validacao']
            and validation['sha256_script'] == origin['sha256_script_validacao']
            and validation['checkpoint'] == profile['checkpoint']['diretorio'], 'Relatório 06 incompatível.')
    audit_key = 'auditoria_preprocessamento'
    require(origin[audit_key] == old_profile['origem'][audit_key]
            and origin['sha256_' + audit_key] == old_profile['origem']['sha256_' + audit_key], 'Auditoria alterada.')
    material = previous.preflight(root, old_profile)
    audit = json.loads(training.checked(root, origin, audit_key))
    expected_path = (Path(old_profile['origem']['validacao']).parent / 'teste_cpc.jsonl').as_posix()
    require(origin['teste'] == expected_path and origin['sha256_teste'] == audit['sha256_arquivos']['teste_cpc.jsonl'],
            'O teste deve ser a partição congelada pelo pré-processamento.')
    data = training.checked(root, origin, 'teste')
    records = [json.loads(line) for line in data.decode('utf-8').splitlines() if line.strip()]
    require(len(records) == 20, 'Esperadas 20 famílias de teste.')
    validation_ids = {row['id_familia_docdb'] for row in material['records']}
    seen = set()
    for row in records:
        family = row['id_familia_docdb']
        require(isinstance(family, str) and family.isdigit() and int(family) > 0
                and family not in seen and family not in validation_ids, 'Família inválida, duplicada ou sobreposta à validação.')
        seen.add(family)
        require(row['particao'] == 'teste', 'Arquivo contém outra partição.')
        require(bool(re.fullmatch(previous.CPC_PATTERN, canonical_cpc(row['alvo_cpc_proxy']))), 'Alvo CPC inválido.')
        for field in ('titulo', 'resumo'):
            require(row['entrada']['idiomas'][field] in {'pt', 'en'}
                    and bool(row['entrada']['textos'][field].strip()), 'Texto ou idioma inválido.')
    material['records'] = sorted(records, key=lambda row: int(row['id_familia_docdb']))
    material['provenance'] = {'particao': 'teste', 'teste_aberto': True,
        'hashes_origem': {key: origin['sha256_' + key] for key in ORIGIN_KEYS},
        'sha256_manifest_checkpoint': profile['checkpoint']['sha256_manifest'],
        'procedimento_identico_06': True,
        'nota': 'Teste final do piloto; não reajustar o procedimento a partir destes resultados.'}
    return material


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
                     "limite": "Teste final do piloto CPC: amostra de 20 famílias; não demonstra qualidade de extração."}
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
            checkpoint=profile["checkpoint"]["diretorio"], familias_por_variante=20, teste_aberto=True)
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
                    result.update(id_familia_docdb=row["id_familia_docdb"], variante=variant, particao="teste",
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
            estado="avaliacao_cpc_teste_concluida", etapa="concluido", teste_executado=True)
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
        print("RESUMO DO TESTE CPC — copie este bloco", flush=True)
        print(json.dumps({key: reporter.data.get(key) for key in fields}, ensure_ascii=False, indent=2), flush=True)
        print("Relatório completo: " + str(reporter.path), flush=True)
    return code, reporter.path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz", type=Path, required=True)
    parser.add_argument("--perfil", default="config/perfil_avaliacao_cpc_teste.json")
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
