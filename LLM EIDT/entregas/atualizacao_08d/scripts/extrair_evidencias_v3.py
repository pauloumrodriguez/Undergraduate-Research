"""08c: duas famílias, elementos e relações, JSON guiado e evidência por trecho."""
from __future__ import annotations
import argparse
from contextlib import nullcontext
import copy
from datetime import datetime, timezone
from importlib import metadata
import json
import os
from pathlib import Path
import random
import sys
import time
import extrair_evidencias_v2 as history
import extrair_evidencias as old
import treinar_qlora_cpc as training
import testar_qlora_gpu as helper

require, sha256 = helper.require, helper.sha256
RESULTS='resultados/etapa_5c/piloto_br_200'
GROUPS=('memes_tecnicos','funcoes','materiais','processos')
PREFIXES=dict(memes_tecnicos='meme',funcoes='funcao',materiais='material',processos='processo')
GENERATION=dict(max_prompt_tokens=3072,max_new_tokens=1024,contexto_total=4096,do_sample=False,
    num_beams=1,use_cache=True,enable_thinking=False,repeat_window=32,repeat_count=3)

def choose_two(records):
    ordered=sorted(records,key=lambda r:(sum(len(r['textos'][f]) for f in ('titulo','resumo')),int(r['id_familia_docdb'])))
    require(len(ordered)==6,'Esperadas seis famílias do 08b.')
    return [ordered[0],ordered[-1]]

def preflight(root,profile,checkpoint=True):
    require(profile['id']=='br_patstat_200_extracao_validacao2_v3' and profile['resultados']==RESULTS
        and profile['geracao']==GENERATION and profile['semente']==42,'Perfil 08c divergente.')
    raw={k:training.checked(root,profile['origem'],k) for k in profile['origem'] if not k.startswith('sha256_')}
    require(raw['script_08b']==Path(history.__file__).read_bytes(),'Script 08b importado divergente.')
    previous=json.loads(raw['perfil_08b'])
    require(all(profile[k]==previous[k] for k in ('modelo','quantizacao','checkpoint')),'Modelo/checkpoint alterado.')
    material=history.preflight(root,previous,checkpoint=checkpoint)
    material['records']=choose_two(material['records'])
    require([r['id_familia_docdb'] for r in material['records']]==profile['amostra']['ids'],'Amostra alterada.')
    material['schema_canonico']=material['schema']['canonico']
    material['templates']=json.loads(raw['schemas'])
    material['instructions']={s:raw['prompt_'+s].decode('utf-8') for s in ('elementos','relacoes')}
    return material

def source_spans(row,maximum=256):
    """Cobertura integral sem normalização, remoção ou sobreposição; cortes preferem espaços."""
    spans=[]
    for field,prefix in (('titulo','T'),('resumo','R')):
        text=row['textos'][field]; start=0; count=1
        while start<len(text):
            end=min(len(text),start+maximum)
            if end<len(text):
                split=text.rfind(' ',start+maximum//2,end)
                if split>=0: end=split+1
            spans.append(dict(id=f'{prefix}{count:03}',campo=field,texto=text[start:end],
                idioma=row['idiomas'][field],inicio=start,fim=end))
            start=end; count+=1
        require(''.join(s['texto'] for s in spans if s['campo']==field)==text,'Cobertura de texto incompleta.')
    return spans

def array(items,**kw): return dict(type='array',items=items,**kw)
def object_schema(properties): return dict(type='object',properties=properties,required=list(properties),additionalProperties=False)

def stage_schema(stage,spans,templates,elements=None):
    refs={'type':'string','enum':[s['id'] for s in spans]}
    evidence=array(refs,minItems=1,uniqueItems=True)
    if stage=='elementos':
        item=copy.deepcopy(templates['elemento'])
        item['properties']['evidencias']=evidence
        return object_schema({f:array(copy.deepcopy(item)) for f in GROUPS})
    require(elements is not None,'Relações exigem elementos válidos.')
    meme_ids=[x['id'] for x in elements['memes_tecnicos']]
    all_ids=[x['id'] for f in GROUPS for x in elements[f]]
    pair=copy.deepcopy(templates['par']); effect=copy.deepcopy(templates['efeito'])
    pair['properties']['memes']=array({'type':'string','enum':meme_ids or ['indisponivel']},minItems=2,maxItems=2,uniqueItems=True)
    pair['properties']['evidencias']=copy.deepcopy(evidence)
    effect['properties']['evidencias']=copy.deepcopy(evidence)
    effect['properties']['relacionado_a']=array({'type':'string','enum':all_ids or ['indisponivel']},uniqueItems=True,
        **({'maxItems':0} if not all_ids else {}))
    return object_schema(dict(pares_convergencia=array(pair,**({'maxItems':0} if len(meme_ids)<2 else {})),efeitos=array(effect)))

def prepare_prompt(tokenizer,row,spans,stage,instruction,schema,elements=None):
    payload=dict(trechos=[{k:s[k] for k in ('id','campo','idioma','texto')} for s in spans])
    if elements is not None: payload['elementos']=elements
    messages=[dict(role='system',content=instruction+'\nSCHEMA_OBRIGATORIO\n'+json.dumps(schema,ensure_ascii=False,separators=(',',':'))),
        dict(role='user',content='DADOS_DA_PATENTE_JSON\n'+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\nFIM_DOS_DADOS_DA_PATENTE_JSON')]
    text=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    ids=tokenizer(text,add_special_tokens=False)['input_ids']
    require(0<len(ids)<=GENERATION['max_prompt_tokens'],'Prompt excede 3072 tokens; interromper sem recortar.')
    return dict(texto=text,input_ids=ids,attention_mask=[1]*len(ids),tokens=len(ids),sha256_prompt=sha256(text.encode()))

def canonical_elements(obj):
    return {f:[dict(id=f'{PREFIXES[f]}_{i}',**copy.deepcopy(item)) for i,item in enumerate(obj[f],1)] for f in GROUPS}

def validate_stage(raw,row,spans,stage,schema,canonical_schema,elements=None):
    from jsonschema import Draft202012Validator
    errors=[]; obj=None; parsed=False
    if not raw['terminou_em_eos']: errors.append('geracao_sem_eos')
    if raw['repeticao_detectada']: errors.append('repeticao_detectada')
    if raw['especial_inesperado']: errors.append('token_especial_inesperado')
    try: obj=old.strict_json(raw['texto_avaliado']); parsed=True
    except (ValueError,RecursionError) as exc: errors.append('json_invalido: '+str(exc)[:250])
    schema_ok=False
    if parsed:
        violations=list(Draft202012Validator(schema).iter_errors(obj))
        errors.extend('schema: '+str(list(v.absolute_path))+': '+v.message[:200] for v in violations)
        schema_ok=not violations
    compact=None; canonical=None
    if schema_ok:
        bank={s['id']:s for s in spans}
        groups=GROUPS if stage=='elementos' else ('pares_convergencia','efeitos')
        for group in groups:
            seen=set()
            for item in obj[group]:
                key=json.dumps(item,ensure_ascii=False,sort_keys=True)
                if key in seen: errors.append(group+': item_duplicado')
                seen.add(key)
                if 'idioma' in item and item['idioma'] not in {bank[x]['idioma'] for x in item['evidencias']}:
                    errors.append(group+': idioma_sem_suporte')
        if not errors:
            compact=canonical_elements(obj) if stage=='elementos' else {
                'pares_convergencia':[dict(id=f'par_{i}',**copy.deepcopy(x)) for i,x in enumerate(obj['pares_convergencia'],1)],
                'efeitos':[dict(id=f'efeito_{i}',**copy.deepcopy(x)) for i,x in enumerate(obj['efeitos'],1)]}
            if stage=='relacoes':
                canonical=dict(versao_schema='patstat-br-extracao-1.0',id_familia_docdb=row['id_familia_docdb'],
                    idiomas_entrada=row['idiomas'],**copy.deepcopy(elements),**copy.deepcopy(compact))
                for group in old.FIELDS:
                    for item in canonical[group]:
                        item['evidencias']=[{k:bank[ref][k] for k in ('campo','texto','idioma','inicio','fim')} for ref in item['evidencias']]
                checked=old.validate_response(json.dumps(canonical,ensure_ascii=False),row,canonical_schema)
                errors.extend(checked['erros'])
    valid=not errors
    return dict(json_parseavel=parsed,schema_valido=schema_ok,etapa_valida=valid,erros=errors,
        itens_validados=compact if valid else None,extracao_validada=canonical if valid else None,
        qualidade_semantica='pendente_revisao_humana')

def repeated_suffix(tokens,window=32,count=3):
    return len(tokens)>=window*count and all(tokens[-window:]==tokens[-window*i:-window*(i-1)] for i in range(2,count+1))

def grammar_parser(schema,text=''):
    from lmformatenforcer import JsonSchemaParser,CharacterLevelParserConfig
    from lmformatenforcer.consts import COMPLETE_ALPHABET
    # Acrescentar latim/acentos e todos os caracteres imprimíveis do prompt evita viés ASCII.
    alphabet=''.join(sorted(set(COMPLETE_ALPHABET+''.join(chr(i) for i in range(160,592))+''.join(c for c in text if c.isprintable()))))
    cfg=CharacterLevelParserConfig(alphabet=alphabet,max_consecutive_whitespaces=1,
        force_json_field_order=True,max_json_array_length=1024)
    return JsonSchemaParser(schema,config=cfg)

def generate_one(torch,model,tokenizer,tokenizer_data,prompt,schema,variant,device='cuda:0'):
    from transformers import GenerationConfig,StoppingCriteria,StoppingCriteriaList
    from lmformatenforcer.integrations.transformers import build_transformers_prefix_allowed_tokens_fn
    require(variant in ('base','adaptado') and model.get_model_status().enabled is True
        and model.get_model_status().merged_adapters==[],'Estado de adaptador inválido.')
    prefix=build_transformers_prefix_allowed_tokens_fn(tokenizer_data,grammar_parser(schema,prompt['texto']))
    class RepeatStop(StoppingCriteria):
        detected=False
        def __call__(self,input_ids,scores,**kwargs):
            self.detected=repeated_suffix(input_ids[0,prompt['tokens']:].tolist())
            return self.detected
    stop=RepeatStop()
    options=GenerationConfig(do_sample=False,num_beams=1,max_new_tokens=1024,use_cache=True,
        eos_token_id=tokenizer.eos_token_id,pad_token_id=tokenizer.eos_token_id,bos_token_id=tokenizer.bos_token_id,
        return_dict_in_generate=False,output_scores=False)
    batch={k:torch.tensor([prompt[k]],dtype=torch.long,device=device) for k in ('input_ids','attention_mask')}
    try:
        with model.disable_adapter() if variant=='base' else nullcontext():
            require(model.get_model_status().enabled is (variant=='adaptado'),'Alternância falhou.')
            with torch.inference_mode(),training.amp_context(torch,device,torch.float16 if device.startswith('cuda') else None):
                result=model.generate(**batch,generation_config=options,logits_to_keep=1,
                    prefix_allowed_tokens_fn=prefix,stopping_criteria=StoppingCriteriaList([stop]))
            full=result[0].detach().cpu().tolist(); del result
    finally:
        model.requires_grad_(False); model.eval(); del batch
    require(model.get_model_status().enabled is True,'Adaptador não restaurado.')
    require(full[:prompt['tokens']]==prompt['input_ids'],'Prefixo alterado.')
    generated=full[prompt['tokens']:]; require(0<len(generated)<=1024,'Quantidade de tokens inválida.')
    eos=generated[-1]==tokenizer.eos_token_id; content=generated[:-1] if eos else generated
    return dict(ids_gerados=generated,texto_bruto=tokenizer.decode(generated,skip_special_tokens=False,clean_up_tokenization_spaces=False),
        texto_avaliado=tokenizer.decode(content,skip_special_tokens=False,clean_up_tokenization_spaces=False),
        tokens_gerados=len(generated),terminou_em_eos=eos,atingiu_limite=len(generated)==1024 and not eos,
        repeticao_detectada=bool(stop.detected),especial_inesperado=any(t in set(tokenizer.all_special_ids) for t in content))

def load_saved(path,identity,validator):
    envelope=json.loads(path.read_bytes()); result=envelope['conteudo']
    require(sha256(helper.json_bytes(result))==envelope['sha256_conteudo'],'Resposta salva alterada.')
    require(all(result[k]==v for k,v in identity.items()),'Resposta de outro perfil/prompt/etapa.')
    expected=validator(result)
    require(all(result[k]==v for k,v in expected.items()),'Validação salva divergente.')
    return result

def summarize(pipelines):
    return {v:dict(familias_previstas=2,familias_processadas=sum(p['variante']==v for p in pipelines),
        elementos_validos=sum(p['variante']==v and p['elementos_validos'] for p in pipelines),
        extracoes_validas=sum(p['variante']==v and p['extracao_valida'] for p in pipelines),
        relacoes_bloqueadas=sum(p['variante']==v and p['relacoes_bloqueadas'] for p in pipelines)) for v in ('base','adaptado')}

def run(root,profile_relative):
    started=time.perf_counter(); profile_bytes=training.safe_path(root,profile_relative).read_bytes(); profile=json.loads(profile_bytes)
    directory=training.safe_path(root,RESULTS+'/extracao_'+sha256(profile_bytes)[:16]); directory.mkdir(parents=True,exist_ok=True)
    lock=directory/'em_execucao.lock'
    with lock.open('x',encoding='utf-8') as stream: stream.write(datetime.now(timezone.utc).isoformat())
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    report=dict(estado='extracao08c_iniciada',etapa='integridade',erro=None,perfil=profile,sha256_perfil=sha256(profile_bytes),
        sha256_script=sha256(Path(__file__).read_bytes()),familias=2,geracoes_maximas=8,geracoes_concluidas=0,
        retomadas_do_drive=0,treinamento_executado=False,teste_extracao_executado=False,
        pasta_execucao=directory.relative_to(root).as_posix(),qualidade_semantica='pendente_revisao_humana')
    torch=None; model=None; calls=[]; pipelines=[]; code=1
    def save():
        report['geracoes_concluidas']=len(calls); report['metricas_automaticas']=summarize(pipelines)
        training.atomic_json(directory/'relatorio.json',report)
        training.atomic_json(directory/('chamada_'+stamp+'.json'),report)
    def phase(name): report['etapa']=name; save(); print('08c: '+name,flush=True)
    try:
        material=preflight(root,profile)
        versions={n:metadata.version(n) for n in (*training.PACKAGES,'jsonschema','lm-format-enforcer','interegular','pydantic')}
        for n,v in {**helper.EXPECTED_PACKAGES,'jsonschema':'4.25.1','lm-format-enforcer':'0.11.3','interegular':'0.3.3'}.items():
            require(versions[n]==v,f'Instale {n}=={v}.')
        import torch as torch_module
        torch=torch_module; require(torch.cuda.is_available(),'Selecione GPU.')
        torch.cuda.set_device(0); torch.manual_seed(42); torch.cuda.manual_seed_all(42); random.seed(42)
        torch.backends.cuda.matmul.allow_tf32=False; torch.backends.cudnn.allow_tf32=False; torch.backends.cudnn.benchmark=False
        torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats(0)
        report['ambiente']=dict(python=sys.version,pacotes=versions,gpu=torch.cuda.get_device_name(0))
        fingerprint=dict(perfil=report['sha256_perfil'],script=report['sha256_script'],ambiente=report['ambiente'])
        manifest=directory/'execucao.json'
        if manifest.exists(): require(json.loads(manifest.read_bytes())==fingerprint,'Ambiente/código divergente na retomada.')
        else: training.atomic_json(manifest,fingerprint)
        from transformers import AutoTokenizer,AutoModelForCausalLM,BitsAndBytesConfig
        from peft import PeftModel,prepare_model_for_kbit_training
        from lmformatenforcer.integrations.transformers import build_token_enforcer_tokenizer_data
        common=dict(revision=profile['modelo']['revisao'],trust_remote_code=False,cache_dir=str(Path(os.environ.get('HF_HOME','/content/hf_cache_llm_eidt_br'))/'hub'))
        phase('tokenizador_e_gramatica')
        tokenizer=AutoTokenizer.from_pretrained(profile['modelo']['id'],**common)
        require(tokenizer.eos_token_id is not None,'Tokenizador sem EOS.')
        tokenizer_data=build_token_enforcer_tokenizer_data(tokenizer)
        old.export_review(directory,material['records'],[])
        for row in material['records']:
            family=row['id_familia_docdb']; spans=source_spans(row)
            training.atomic_json(directory/'trechos'/f'{family}.json',dict(familia=family,textos=row['textos'],trechos=spans))
            for variant in ('base','adaptado'):
                elements=None; stages=[]
                for stage in ('elementos','relacoes'):
                    if stage=='relacoes' and not stages[0]['etapa_valida']: break
                    schema=stage_schema(stage,spans,material['templates'],elements)
                    prompt=prepare_prompt(tokenizer,row,spans,stage,material['instructions'][stage],schema,elements)
                    identity=dict(id_familia_docdb=family,variante=variant,etapa=stage,sha256_perfil=report['sha256_perfil'],
                        sha256_prompt=prompt['sha256_prompt'],sha256_schema=sha256(helper.json_bytes(schema)))
                    training.atomic_json(directory/'prompts'/f'{family}_{variant}_{stage}.json',dict(prompt=prompt,schema=schema))
                    path=directory/'respostas'/f'{family}_{variant}_{stage}.json'
                    validator=lambda output:validate_stage(output,row,spans,stage,schema,material['schema_canonico'],elements)
                    if path.exists():
                        result=load_saved(path,identity,validator); report['retomadas_do_drive']+=1
                    else:
                        if model is None:
                            phase('carregamento')
                            quant=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.float16)
                            base=AutoModelForCausalLM.from_pretrained(profile['modelo']['id'],**common,low_cpu_mem_usage=True,
                                quantization_config=quant,torch_dtype=torch.float16,device_map={'':0},attn_implementation='sdpa')
                            require(getattr(base,'is_loaded_in_4bit',False),'Quantização ausente.')
                            base=prepare_model_for_kbit_training(base,use_gradient_checkpointing=False)
                            model=PeftModel.from_pretrained(base,str(material['checkpoint_directory']/'adapter'),is_trainable=False,autocast_adapter_dtype=True)
                            model.requires_grad_(False); model.eval()
                            require(all(p.device.type=='cuda' for p in model.parameters()),'Offload não previsto.')
                            torch.cuda.empty_cache(); report['memoria_apos_carregamento']=helper.memory_snapshot(torch)
                        phase(f'geracao_{family}_{variant}_{stage}')
                        raw=generate_one(torch,model,tokenizer,tokenizer_data,prompt,schema,variant)
                        result={**identity,**raw,**validator(raw)}
                        old.save_result(path,result)
                    calls.append(result); stages.append(result); save()
                    if stage=='elementos': elements=result['itens_validados']
                    print(f'{family} {variant} {stage}: valida={result["etapa_valida"]}; chamadas={len(calls)}',flush=True)
                valid=len(stages)==2 and stages[1]['etapa_valida']
                pipelines.append(dict(id_familia_docdb=family,variante=variant,elementos_validos=stages[0]['etapa_valida'],
                    relacoes_bloqueadas=len(stages)==1,extracao_valida=valid,
                    extracao_validada=stages[-1]['extracao_validada'] if valid else None,
                    etapas=[dict(etapa=s['etapa'],valida=s['etapa_valida'],erros=s['erros']) for s in stages]))
                save()
        require(len(pipelines)==4,'Pipelines incompletos.')
        for name,items in (('extracoes.jsonl',pipelines),('geracoes.jsonl',calls)):
            (directory/name).write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in items),encoding='utf-8')
        review=[]
        for pipeline in pipelines:
            related=[c for c in calls if c['id_familia_docdb']==pipeline['id_familia_docdb'] and c['variante']==pipeline['variante']]
            review.append(dict(id_familia_docdb=pipeline['id_familia_docdb'],variante=pipeline['variante'],
                texto_avaliado='\n\n'.join(c['etapa']+': '+c['texto_avaliado'] for c in related),
                erros=[error for c in related for error in c['erros']]))
        old.export_review(directory,material['records'],review)
        report.update(estado='extracao08c_concluida_revisao_pendente',etapa='concluido',
            sha256_arquivos={n:sha256((directory/n).read_bytes()) for n in ('extracoes.jsonl','geracoes.jsonl')},
            aviso='Trechos e estrutura válidos não comprovam suporte semântico; nenhum modelo foi selecionado.')
        code=0
    except (Exception,KeyboardInterrupt) as exc:
        report.update(estado='extracao08c_interrompida',etapa_falha=report['etapa'],erro=dict(tipo=type(exc).__name__,mensagem=helper.safe_error_message(exc)))
    finally:
        if torch is not None and torch.cuda.is_available():
            try: report['memoria_final']=helper.memory_snapshot(torch)
            except Exception as exc: report['erro_medicao_memoria']=type(exc).__name__
        report['duracao_chamada_segundos']=round(time.perf_counter()-started,2)
        try: save()
        finally: lock.unlink(missing_ok=True)
        print('RESUMO DO 08c — copie este bloco',flush=True)
        print(json.dumps({k:report.get(k) for k in ('estado','geracoes_concluidas','metricas_automaticas','retomadas_do_drive','memoria_final','erro')},ensure_ascii=False,indent=2),flush=True)
        print('Relatório: '+str(directory/'relatorio.json'),flush=True)
    return code

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raiz',type=Path,required=True)
    parser.add_argument('--perfil',default='config/perfil_extracao_validacao2_v3.json')
    parser.add_argument('--validar_apenas',action='store_true')
    args=parser.parse_args(); root=args.raiz.resolve()
    if args.validar_apenas:
        profile=json.loads(training.safe_path(root,args.perfil).read_bytes()); material=preflight(root,profile)
        print(json.dumps(dict(estado='integridade_extracao_aprovada',familias=2,ids=[r['id_familia_docdb'] for r in material['records']],checkpoint=profile['checkpoint']['diretorio'])))
    else: raise SystemExit(run(root,args.perfil))

if __name__=='__main__': main()
