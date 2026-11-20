"""Piloto de extração em seis validações; comparação pareada, sem treino."""
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
FIELDS = ('memes_tecnicos', 'pares_convergencia', 'funcoes', 'materiais', 'processos', 'efeitos')
RESULTS = 'resultados/etapa_5/piloto_br_200'
GENERATION = dict(max_prompt_tokens=2048, max_new_tokens=2048, contexto_total=4096,
                  do_sample=False, num_beams=1, use_cache=True, enable_thinking=False)


def select_records(records):
    """Seleção por hash, independente do conteúdo e das previsões CPC."""
    require(len(records) == 200, 'Esperadas 200 entradas congeladas.')
    ids = [r['id_familia_docdb'] for r in records]
    require(len(set(ids)) == 200, 'Famílias duplicadas nas entradas.')
    chosen = []
    for window in ('2010-2014', '2015-2019', '2020-2024'):
        group = [r for r in records if r['particao'] == 'validacao' and r['janela'] == window]
        require(len(group) >= 2, 'Estrato sem duas validações.')
        chosen.extend(sorted(group, key=lambda r: sha256(('08|42|' + r['id_familia_docdb']).encode()))[:2])
    return sorted(chosen, key=lambda r: int(r['id_familia_docdb']))


def preflight(root, profile, checkpoint=True):
    require(profile['id'] == 'br_patstat_200_extracao_validacao6_v1'
            and profile['resultados'] == RESULTS and profile['geracao'] == GENERATION,
            'Perfil de extração divergente.')
    require(profile['semente'] == 42 and profile['amostra']['familias'] == 6
            and profile['amostra']['particao'] == 'validacao', 'Amostra divergente.')
    raw = {k: training.checked(root, profile['origem'], k) for k in profile['origem'] if not k.startswith('sha256_')}
    require(raw['script_cpc'] == Path(cpc.__file__).read_bytes(), 'Script CPC importado divergente.')
    previous = json.loads(raw['perfil_cpc'])
    for key in ('modelo', 'quantizacao', 'checkpoint'):
        require(profile[key] == previous[key], 'Mudança de modelo/adaptador: ' + key)
    audit = json.loads(raw['auditoria'])
    require(sha256(raw['entradas']) == audit['sha256_arquivos']['entradas_extracao.jsonl']
            and sha256(raw['schema']) == audit['sha256_schema']
            and sha256(raw['prompt']) == audit['sha256_prompt'], 'Pré-processamento divergente.')
    records = select_records([json.loads(line) for line in raw['entradas'].decode('utf-8').splitlines() if line.strip()])
    require([r['id_familia_docdb'] for r in records] == profile['amostra']['ids'], 'Seleção alterada.')
    for row in records:
        require(set(row['textos']) == set(row['idiomas']) == {'titulo', 'resumo'}, 'Entrada incompleta.')
        require(all(isinstance(t, str) and t.strip() for t in row['textos'].values()), 'Texto vazio.')
        require(all(v in ('pt', 'en') for v in row['idiomas'].values()), 'Idioma não previsto.')
    material = cpc.preflight(root, previous) if checkpoint else None
    if material:
        valid = {r['id_familia_docdb']: r['entrada'] for r in material['records']}
        require(all(r['id_familia_docdb'] in valid and all(r[k] == valid[r['id_familia_docdb']][k]
                    for k in ('textos', 'idiomas')) for r in records), 'Textos diferem da validação congelada.')
    return dict(records=records, instruction=raw['prompt'].decode('utf-8'), schema=json.loads(raw['schema']),
                checkpoint_directory=material['checkpoint_directory'] if material else None)


def build_prompt(tokenizer, row, instruction):
    payload = {k: row[k] for k in ('id_familia_docdb', 'idiomas', 'textos')}
    messages = [dict(role='system', content=instruction), dict(role='user', content=
        'DADOS_DA_PATENTE_JSON\n' + json.dumps(payload, ensure_ascii=False) + '\nFIM_DOS_DADOS_DA_PATENTE_JSON')]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    ids = tokenizer(text, add_special_tokens=False)['input_ids']
    require(0 < len(ids) <= GENERATION['max_prompt_tokens'], 'Prompt longo: revisar perfil; nenhum recorte automático.')
    return dict(texto=text, input_ids=ids, attention_mask=[1]*len(ids), tokens=len(ids), sha256_prompt=sha256(text.encode()))


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Chave JSON duplicada: ' + key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('Constante JSON inválida: ' + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)


def validate_response(text, row, schema, eos=True, special=False):
    """Valida estrutura e suporte literal; nunca corrige a resposta nem julga semântica."""
    from jsonschema import Draft202012Validator
    errors = []
    if not eos:
        errors.append('geracao_sem_eos')
    if special:
        errors.append('token_especial_inesperado')
    obj = None
    parsed = False
    try:
        obj = strict_json(text)
        parsed = True
    except (ValueError, RecursionError) as exc:
        errors.append('json_invalido: ' + str(exc)[:300])
    schema_ok = False
    if parsed:
        violations = list(Draft202012Validator(schema).iter_errors(obj))
        errors.extend('schema: ' + '/'.join(map(str, e.absolute_path)) + ': ' + e.message[:200] for e in violations)
        schema_ok = not violations
    if schema_ok:
        if obj['id_familia_docdb'] != row['id_familia_docdb']:
            errors.append('familia_divergente')
        if obj['idiomas_entrada'] != row['idiomas']:
            errors.append('idiomas_divergentes')
        all_items = [item for field in FIELDS for item in obj[field]]
        identifiers = [item['id'] for item in all_items]
        if len(identifiers) != len(set(identifiers)):
            errors.append('ids_duplicados')
        memes = {x['id'] for x in obj['memes_tecnicos']}
        targets = {x['id'] for f in ('memes_tecnicos', 'funcoes', 'materiais', 'processos') for x in obj[f]}
        pairs_seen = set()
        for item in all_items:
            for ev in item['evidencias']:
                original = row['textos'][ev['campo']]
                if not (0 <= ev['inicio'] < ev['fim'] <= len(original)) or original[ev['inicio']:ev['fim']] != ev['texto']:
                    errors.append(item['id'] + ': intervalo_ou_citacao_incorretos')
                if ev['idioma'] != row['idiomas'][ev['campo']]:
                    errors.append(item['id'] + ': idioma_evidencia_divergente')
            if 'idioma' in item and item['idioma'] not in {e['idioma'] for e in item['evidencias']}:
                errors.append(item['id'] + ': idioma_item_sem_suporte')
        for pair in obj['pares_convergencia']:
            key = tuple(sorted(pair['memes']))
            if not set(key).issubset(memes):
                errors.append(pair['id'] + ': referencia_meme_inexistente')
            if key in pairs_seen:
                errors.append(pair['id'] + ': par_repetido')
            pairs_seen.add(key)
        for effect in obj['efeitos']:
            if not set(effect['relacionado_a']).issubset(targets):
                errors.append(effect['id'] + ': referencia_efeito_inexistente')
    valid = not errors
    return dict(json_parseavel=parsed, schema_valido=schema_ok,
                estrutura_e_evidencias_validas=valid, erros=errors,
                extracao_validada=obj if valid else None,
                contagens={f: len(obj[f]) for f in FIELDS} if valid else None,
                qualidade_semantica='pendente_revisao_humana')


def generate_one(torch, model, tokenizer, prompt, variant, device='cuda:0'):
    from transformers import GenerationConfig
    require(variant in ('base', 'adaptado'), 'Variante desconhecida.')
    require(model.get_model_status().enabled is True and model.get_model_status().merged_adapters == [], 'Adaptador mesclado/inativo.')
    options = GenerationConfig(do_sample=False, num_beams=1, max_new_tokens=2048, use_cache=True,
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
    require(0 < len(generated) <= 2048, 'Geração de tamanho inválido.')
    eos = generated[-1] == tokenizer.eos_token_id
    content = generated[:-1] if eos else generated
    return dict(ids_gerados=generated, texto_bruto=tokenizer.decode(generated, skip_special_tokens=False, clean_up_tokenization_spaces=False),
        texto_avaliado=tokenizer.decode(content, skip_special_tokens=False, clean_up_tokenization_spaces=False),
        terminou_em_eos=eos, atingiu_limite=len(generated) == 2048 and not eos,
        especial_inesperado=any(t in set(tokenizer.all_special_ids) for t in content), tokens_gerados=len(generated))


def save_result(path, value):
    """Envelope permite detectar edição/corrupção na retomada."""
    require(not path.exists(), 'Resposta já existente: não substituir.')
    training.atomic_json(path, dict(sha256_conteudo=sha256(helper.json_bytes(value)), conteudo=value))


def load_result(path, identity, row, schema):
    envelope = json.loads(path.read_bytes())
    result = envelope['conteudo']
    require(sha256(helper.json_bytes(result)) == envelope['sha256_conteudo'], 'Resposta salva alterada.')
    require(all(result[k] == v for k, v in identity.items()), 'Resposta pertence a outra execução/prompt.')
    expected = validate_response(result['texto_avaliado'], row, schema, result['terminou_em_eos'], result['especial_inesperado'])
    require(all(result[k] == v for k, v in expected.items()), 'Validação salva divergente.')
    return result


def summary(results):
    out = {}
    for variant in ('base', 'adaptado'):
        rows = [x for x in results if x['variante'] == variant]
        out[variant] = dict(previstas=6, concluidas=len(rows), json_parseavel=sum(x['json_parseavel'] for x in rows),
            schema_valido=sum(x['schema_valido'] for x in rows),
            estrutura_e_evidencias_validas=sum(x['estrutura_e_evidencias_validas'] for x in rows),
            limites_atingidos=sum(x['atingiu_limite'] for x in rows))
    return out


def export_review(directory, records, predictions):
    """Anotação independente primeiro; candidatos A/B não contêm nome do modelo."""
    gold = directory / 'anotacao_independente.jsonl'
    templates = [dict(id_familia_docdb=r['id_familia_docdb'], textos=r['textos'], idiomas=r['idiomas'],
        anotador=None, revisao_concluida=False, anotacao={f: None for f in FIELDS}) for r in records]
    if not gold.exists():
        gold.write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in templates), encoding='utf-8')
    keys, rows = [], []
    by_id = {r['id_familia_docdb']: r for r in records}
    for item in predictions:
        family = item['id_familia_docdb']
        flip = int(sha256(('cego08|' + family).encode())[:8], 16) % 2
        label = ('A', 'B')[int(item['variante'] == 'adaptado') ^ flip]
        keys.append(dict(id_familia_docdb=family, candidato=label, variante=item['variante']))
        rows.append(dict(id_familia_docdb=family, candidato=label, titulo=by_id[family]['textos']['titulo'],
            resumo=by_id[family]['textos']['resumo'], resposta_bruta=item['texto_avaliado'],
            erros_automaticos=json.dumps(item['erros'], ensure_ascii=False),
            anotador='', suporte_semantico='', omissoes='', convergencia_e_efeitos='', observacoes=''))
    if rows:
        output = io.StringIO(newline='')
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in sorted(rows, key=lambda r: (int(r['id_familia_docdb']), r['candidato'])):
            writer.writerow({k: "'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@')) else v for k,v in row.items()})
        target = directory / 'revisao_cega_modelos.csv'
        # Não sobrescrever comentários humanos em uma retomada.
        if not target.exists():
            target.write_bytes(output.getvalue().encode('utf-8-sig'))
        training.atomic_json(directory / 'chave_variantes_nao_enviar_ao_anotador.json', keys)


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
    parser.add_argument('--perfil', default='config/perfil_extracao_validacao6.json')
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
