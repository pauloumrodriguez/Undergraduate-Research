"""08b: citações compartilhadas e posições calculadas por busca literal exata."""
from __future__ import annotations
import argparse
from contextlib import nullcontext
import csv
from datetime import datetime, timezone
from importlib import metadata
import io
import json
import os
from pathlib import Path
import random
import sys
import time

import avaliar_cpc_geracao as cpc
import treinar_qlora_cpc as training
import testar_qlora_gpu as helper

require, sha256 = helper.require, helper.sha256
"""Núcleo da revisão 08b: banco de citações e localização literal auditável."""
import copy
import extrair_evidencias as anterior

FIELDS = anterior.FIELDS
RESULTS = 'resultados/etapa_5b/piloto_br_200'
GENERATION = dict(max_prompt_tokens=2048, max_new_tokens=3072, contexto_total=5120,
                  do_sample=False, num_beams=1, use_cache=True, enable_thinking=False)
strict_json = anterior.strict_json
summary = anterior.summary
export_review = anterior.export_review
save_result = anterior.save_result


def preflight(root, profile, checkpoint=True):
    require(profile['id'] == 'br_patstat_200_extracao_validacao6_v2'
            and profile['resultados'] == RESULTS and profile['geracao'] == GENERATION
            and profile['semente'] == 42, 'Perfil 08b divergente.')
    raw = {k: training.checked(root, profile['origem'], k)
           for k in profile['origem'] if not k.startswith('sha256_')}
    require(raw['script_08'] == Path(anterior.__file__).read_bytes(), 'Dependência 08 alterada.')
    old_profile = json.loads(raw['perfil_08'])
    require(all(profile[k] == old_profile[k] for k in ('modelo', 'quantizacao', 'checkpoint', 'amostra')),
            'O 08b deve preservar modelos, checkpoint e seis famílias do 08.')
    material = anterior.preflight(root, old_profile, checkpoint=checkpoint)
    material['instruction'] = raw['prompt'].decode('utf-8')
    material['schema'] = {'geracao': json.loads(raw['schema']), 'canonico': material['schema']}
    return material


def literal_occurrences(text, quote):
    """Todas as ocorrências, inclusive sobrepostas; sem mudar caixa ou acentos."""
    require(isinstance(quote, str) and bool(quote.strip()), 'Citação vazia.')
    found, offset = [], 0
    while True:
        start = text.find(quote, offset)
        if start == -1:
            return found
        found.append({'inicio': start, 'fim': start + len(quote)})
        offset = start + 1


def validate_response(text, row, schema, eos=True, special=False):
    from jsonschema import Draft202012Validator
    errors, trace = [], []
    parsed, schema_ok, obj, canonical = False, False, None, None
    if not eos:
        errors.append('geracao_sem_eos')
    if special:
        errors.append('token_especial_inesperado')
    try:
        obj = strict_json(text)
        parsed = True
    except (ValueError, RecursionError) as exc:
        errors.append('json_invalido: ' + str(exc)[:300])
    if parsed:
        violations = list(Draft202012Validator(schema['geracao']).iter_errors(obj))
        errors.extend('schema_geracao: ' + '/'.join(map(str,e.absolute_path)) + ': ' + e.message[:200] for e in violations)
        schema_ok = not violations
    if schema_ok:
        bank = {}
        for evidence in obj['evidencias']:
            identifier = evidence['id']
            if identifier in bank:
                errors.append('id_evidencia_duplicado: ' + identifier)
                continue
            quote, field = evidence['texto'], evidence['campo']
            locations = literal_occurrences(row['textos'][field], quote) if quote.strip() else []
            status = 'localizada_unica' if len(locations) == 1 else 'ausente' if not locations else 'ambigua'
            trace.append(dict(id=identifier, campo=field, texto=quote, estado=status, ocorrencias=locations))
            bank[identifier] = None
            if status != 'localizada_unica':
                errors.append(identifier + ': citacao_' + status)
            else:
                bank[identifier] = dict(campo=field, texto=quote, idioma=row['idiomas'][field], **locations[0])
        candidate = {k: copy.deepcopy(obj[k]) for k in ('id_familia_docdb', 'idiomas_entrada', *FIELDS)}
        candidate['versao_schema'] = 'patstat-br-extracao-1.0'
        for field in FIELDS:
            for item in candidate[field]:
                references = item['evidencias']
                for ref in references:
                    if ref not in bank:
                        errors.append(item['id'] + ': referencia_evidencia_inexistente: ' + ref)
                item['evidencias'] = [copy.deepcopy(bank[ref]) for ref in references if bank.get(ref) is not None]
        # Converter somente quando não existe referência ausente/ambígua nem falha de terminação.
        if not errors:
            checked = anterior.validate_response(json.dumps(candidate, ensure_ascii=False), row, schema['canonico'])
            errors.extend(checked['erros'])
            if checked['estrutura_e_evidencias_validas']:
                canonical = candidate
    valid = canonical is not None and not errors
    return dict(json_parseavel=parsed, schema_valido=schema_ok, estrutura_e_evidencias_validas=valid,
        erros=errors, extracao_validada=canonical if valid else None,
        contagens={f:len(canonical[f]) for f in FIELDS} if valid else None,
        localizacao_citacoes=trace, schema_geracao='patstat-br-extracao-2.0',
        schema_normalizado='patstat-br-extracao-1.0', qualidade_semantica='pendente_revisao_humana')


def build_prompt(tokenizer, row, instruction):
    payload = {k: row[k] for k in ('id_familia_docdb', 'idiomas', 'textos')}
    messages = [dict(role='system', content=instruction), dict(role='user', content=
        'DADOS_DA_PATENTE_JSON\n' + json.dumps(payload, ensure_ascii=False) + '\nFIM_DOS_DADOS_DA_PATENTE_JSON')]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    ids = tokenizer(text, add_special_tokens=False)['input_ids']
    require(0 < len(ids) <= GENERATION['max_prompt_tokens'], 'Prompt longo: revisar perfil; nenhum recorte automático.')
    return dict(texto=text, input_ids=ids, attention_mask=[1]*len(ids), tokens=len(ids), sha256_prompt=sha256(text.encode()))

def generate_one(torch, model, tokenizer, prompt, variant, device='cuda:0'):
    from transformers import GenerationConfig
    require(variant in ('base', 'adaptado'), 'Variante desconhecida.')
    require(model.get_model_status().enabled is True and model.get_model_status().merged_adapters == [], 'Adaptador mesclado/inativo.')
    options = GenerationConfig(do_sample=False, num_beams=1, max_new_tokens=3072, use_cache=True,
        eos_token_id=tokenizer.eos_token_id, pad_token_id=tokenizer.eos_token_id,
        bos_token_id=tokenizer.bos_token_id, return_dict_in_generate=False, output_scores=False)
    batch = {k: torch.tensor([prompt[k]], device=device, dtype=torch.long) for k in ('input_ids', 'attention_mask')}
    try:
        with model.disable_adapter() if variant == 'base' else nullcontext():
            require(model.get_model_status().enabled is (variant == 'adaptado'), 'Alternância do adaptador falhou.')
            with torch.inference_mode(), training.amp_context(torch, device, torch.float16 if device.startswith('cuda') else None):
                result = model.generate(**batch, generation_config=options, logits_to_keep=1)
            full = result[0].detach().cpu().tolist()
            require(full[:prompt['tokens']] == prompt['input_ids'], 'Prefixo inesperado.')
            generated = full[prompt['tokens']:]
            del result
    finally:
        model.requires_grad_(False)
        model.eval()
        del batch
    require(model.get_model_status().enabled is True, 'Adaptador não restaurado.')
    require(0 < len(generated) <= 3072, 'Geração de tamanho inválido.')
    eos = generated[-1] == tokenizer.eos_token_id
    content = generated[:-1] if eos else generated
    return dict(ids_gerados=generated, texto_bruto=tokenizer.decode(generated, skip_special_tokens=False, clean_up_tokenization_spaces=False),
        texto_avaliado=tokenizer.decode(content, skip_special_tokens=False, clean_up_tokenization_spaces=False),
        terminou_em_eos=eos, atingiu_limite=len(generated) == 3072 and not eos,
        especial_inesperado=any(t in set(tokenizer.all_special_ids) for t in content), tokens_gerados=len(generated))

def load_result(path, identity, row, schema):
    envelope = json.loads(path.read_bytes())
    result = envelope['conteudo']
    require(sha256(helper.json_bytes(result)) == envelope['sha256_conteudo'], 'Resposta salva alterada.')
    require(all(result[k] == v for k, v in identity.items()), 'Resposta pertence a outra execução/prompt.')
    expected = validate_response(result['texto_avaliado'], row, schema, result['terminou_em_eos'], result['especial_inesperado'])
    require(all(result[k] == v for k, v in expected.items()), 'Validação salva divergente.')
    return result

def run(root, profile_relative):
    start = time.perf_counter()
    profile_bytes = training.safe_path(root, profile_relative).read_bytes()
    profile = json.loads(profile_bytes)
    directory = training.safe_path(root, RESULTS + '/extracao_' + sha256(profile_bytes)[:16])
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / 'em_execucao.lock'
    with lock.open('x', encoding='utf-8') as stream:
        stream.write(datetime.now(timezone.utc).isoformat())
    report = dict(estado='extracao_iniciada', etapa='integridade', erro=None, familias=6, geracoes_previstas=12,
        geracoes_concluidas=0, treinamento_executado=False, particao='validacao', teste_extracao_executado=False,
        pasta_execucao=directory.relative_to(root).as_posix(), perfil=profile,
        sha256_perfil=sha256(profile_bytes), sha256_script=sha256(Path(__file__).read_bytes()),
        limite='Diagnóstico em seis validações. Qualidade semântica e métricas contra referência humana pendentes.')
    torch = None
    predictions = []
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    def save():
        report['geracoes_concluidas'] = len(predictions)
        report['metricas_automaticas'] = summary(predictions)
        training.atomic_json(directory / 'relatorio.json', report)
        training.atomic_json(directory / ('chamada_' + stamp + '.json'), report)
    def phase(name):
        report['etapa'] = name
        save()
        print('Extração: ' + name, flush=True)
    code = 1
    try:
        material = preflight(root, profile)
        phase('ambiente')
        versions = {n: metadata.version(n) for n in (*training.PACKAGES, 'jsonschema')}
        for n, v in {**helper.EXPECTED_PACKAGES, 'jsonschema': '4.25.1'}.items():
            require(versions[n] == v, f'Instale {n}=={v}.')
        import torch as torch_module
        torch = torch_module
        require(torch.cuda.is_available(), 'Selecione GPU no Colab.')
        torch.cuda.set_device(0)
        torch.manual_seed(42)
        torch.cuda.manual_seed_all(42)
        random.seed(42)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cudnn.benchmark = False
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats(0)
        report['ambiente'] = dict(python=sys.version, pacotes=versions, gpu=torch.cuda.get_device_name(0))
        fingerprint = dict(perfil=report['sha256_perfil'], script=report['sha256_script'], ambiente=report['ambiente'])
        manifest = directory / 'execucao.json'
        if manifest.exists():
            require(json.loads(manifest.read_bytes()) == fingerprint, 'Ambiente/código mudou: não misturar respostas na retomada.')
        else:
            training.atomic_json(manifest, fingerprint)
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        from peft import PeftModel, prepare_model_for_kbit_training
        cache = str(Path(os.environ.get('HF_HOME', '/content/hf_cache_llm_eidt_br')) / 'hub')
        common = dict(revision=profile['modelo']['revisao'], cache_dir=cache, trust_remote_code=False)
        tokenizer = AutoTokenizer.from_pretrained(profile['modelo']['id'], **common)
        require(tokenizer.eos_token_id is not None, 'Tokenizador sem EOS.')
        prompts = {r['id_familia_docdb']: build_prompt(tokenizer, r, material['instruction']) for r in material['records']}
        training.atomic_json(directory / 'prompts_auditados.json', prompts)
        report['tokenizacao'] = dict(max_tokens_prompt=max(p['tokens'] for p in prompts.values()), recortadas=0)
        export_review(directory, material['records'], [])
        pending = []
        for row in material['records']:
            for variant in ('base', 'adaptado'):
                identity = dict(id_familia_docdb=row['id_familia_docdb'], variante=variant,
                    sha256_prompt=prompts[row['id_familia_docdb']]['sha256_prompt'], sha256_perfil=report['sha256_perfil'])
                path = directory / 'respostas' / (row['id_familia_docdb'] + '_' + variant + '.json')
                if path.exists():
                    predictions.append(load_result(path, identity, row, material['schema']))
                else:
                    pending.append((row, variant, identity, path))
        report['retomadas_do_drive'] = len(predictions)
        if pending:
            phase('carregamento')
            quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4',
                bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16)
            base = AutoModelForCausalLM.from_pretrained(profile['modelo']['id'], **common,
                low_cpu_mem_usage=True, quantization_config=quant, torch_dtype=torch.float16,
                device_map={'': 0}, attn_implementation='sdpa')
            require(getattr(base, 'is_loaded_in_4bit', False), 'Quantização não aplicada.')
            base = prepare_model_for_kbit_training(base, use_gradient_checkpointing=False)
            model = PeftModel.from_pretrained(base, str(material['checkpoint_directory'] / 'adapter'),
                is_trainable=False, autocast_adapter_dtype=True)
            model.requires_grad_(False)
            model.eval()
            require(all(p.device.type == 'cuda' for p in model.parameters()), 'Offload não previsto.')
            torch.cuda.empty_cache()
            report['memoria_apos_carregamento'] = helper.memory_snapshot(torch)
            for row, variant, identity, path in pending:
                phase('geracao_' + row['id_familia_docdb'] + '_' + variant)
                output = generate_one(torch, model, tokenizer, prompts[row['id_familia_docdb']], variant)
                result = {**identity, **output, **validate_response(output['texto_avaliado'], row, material['schema'],
                    output['terminou_em_eos'], output['especial_inesperado'])}
                save_result(path, result)
                predictions.append(result)
                save()
                print(f"Respostas salvas: {len(predictions)}/12; estrutura/evidências válidas: {result['estrutura_e_evidencias_validas']}", flush=True)
        require(len(predictions) == 12, 'Execução incompleta.')
        predictions.sort(key=lambda r: (int(r['id_familia_docdb']), r['variante']))
        aggregate = directory / 'extracoes.jsonl'
        aggregate.write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in predictions), encoding='utf-8')
        export_review(directory, material['records'], predictions)
        report.update(estado='extracao_piloto_concluida_revisao_pendente', etapa='concluido',
            sha256_extracoes=sha256(aggregate.read_bytes()), anotacao_humana='pendente')
        code = 0
    except (Exception, KeyboardInterrupt) as exc:
        report.update(estado='extracao_interrompida', etapa_falha=report['etapa'],
            erro=dict(tipo=type(exc).__name__, mensagem=helper.safe_error_message(exc)))
    finally:
        if torch is not None and torch.cuda.is_available():
            try:
                report['memoria_final'] = helper.memory_snapshot(torch)
            except Exception as exc:
                report['erro_medicao_memoria'] = type(exc).__name__
        report['duracao_chamada_segundos'] = round(time.perf_counter() - start, 2)
        try:
            save()
        finally:
            lock.unlink(missing_ok=True)
        print('RESUMO DA EXTRAÇÃO — copie este bloco', flush=True)
        print(json.dumps({k: report.get(k) for k in ('estado', 'geracoes_concluidas', 'metricas_automaticas',
            'retomadas_do_drive', 'memoria_final', 'duracao_chamada_segundos', 'erro')}, ensure_ascii=False, indent=2), flush=True)
        print('Relatório: ' + str(directory / 'relatorio.json'), flush=True)
    return code

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raiz', type=Path, required=True)
    parser.add_argument('--perfil', default='config/perfil_extracao_validacao6_v2.json')
    parser.add_argument('--validar_apenas', action='store_true')
    args = parser.parse_args()
    root = args.raiz.resolve()
    if args.validar_apenas:
        profile = json.loads(training.safe_path(root, args.perfil).read_bytes())
        material = preflight(root, profile)
        print(json.dumps(dict(estado='integridade_extracao_aprovada', familias=len(material['records']),
            ids=[r['id_familia_docdb'] for r in material['records']], checkpoint=profile['checkpoint']['diretorio'])))
        return
    raise SystemExit(run(root, args.perfil))

if __name__ == '__main__':
    main()
