"""08d: instruções D1–D5 nas duas famílias do 08c; desenvolvimento pós-revisão."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from importlib import metadata
import json
import os
from pathlib import Path
import random
import sys
import time
import extrair_evidencias_v3 as anterior

training, helper, old = anterior.training, anterior.helper, anterior.old
require, sha256 = helper.require, helper.sha256
GENERATION = dict(anterior.GENERATION)
RESULTS = 'resultados/etapa_5d/piloto_br_200'
source_spans = anterior.source_spans
stage_schema = anterior.stage_schema
prepare_prompt = anterior.prepare_prompt
generate_one = anterior.generate_one
validate_stage = anterior.validate_stage
load_saved = anterior.load_saved
summarize = anterior.summarize

def preflight(root, profile, checkpoint=True):
    require(profile['id']=='br_patstat_200_extracao_validacao2_v4' and profile['versao']=='4.0'
        and profile['resultados']==RESULTS and profile['geracao']==GENERATION, 'Perfil 08d divergente.')
    raw={k:training.checked(root,profile['origem'],k) for k in profile['origem'] if not k.startswith('sha256_')}
    require(raw['script_08c']==Path(anterior.__file__).read_bytes(),'Núcleo 08c importado divergente.')
    prior=json.loads(raw['perfil_08c'])
    for key in ('modelo','quantizacao','checkpoint','semente','geracao','amostra','estrutura','etapas','maximo_geracoes'):
        require(profile[key]==prior[key], '08d deve preservar '+key+' do 08c.')
    require(profile['desenvolvimento']['referencia_usada_na_geracao'] is False
        and profile['desenvolvimento']['pos_exposicao'] is True,'Condição metodológica divergente.')
    material=anterior.preflight(root,prior,checkpoint=checkpoint)
    require(raw['schemas']==training.checked(root,prior['origem'],'schemas'),'Schema alterado.')
    require(raw['requirements']==training.checked(root,prior['origem'],'requirements'),'Dependências alteradas.')
    material['instructions']={s:raw['prompt_'+s].decode('utf-8') for s in ('elementos','relacoes')}
    # Referência anotada não é lida nem incorporada ao material de geração.
    return material

def run(root,profile_relative):
    started=time.perf_counter(); profile_bytes=training.safe_path(root,profile_relative).read_bytes(); profile=json.loads(profile_bytes)
    directory=training.safe_path(root,RESULTS+'/extracao_'+sha256(profile_bytes)[:16]); directory.mkdir(parents=True,exist_ok=True)
    lock=directory/'em_execucao.lock'
    with lock.open('x',encoding='utf-8') as stream: stream.write(datetime.now(timezone.utc).isoformat())
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    report=dict(estado='extracao08d_iniciada',etapa='integridade',erro=None,perfil=profile,sha256_perfil=sha256(profile_bytes),
        sha256_script=sha256(Path(__file__).read_bytes()),familias=2,geracoes_maximas=8,geracoes_concluidas=0,
        retomadas_do_drive=0,treinamento_executado=False,teste_extracao_executado=False,
        pasta_execucao=directory.relative_to(root).as_posix(),qualidade_semantica='pendente_revisao_humana',
        desenvolvimento_pos_exposicao=True,referencia_humana_no_prompt=False,
        regras_aplicadas='D1-D5',sha256_nucleo_08c=profile['origem']['sha256_script_08c'])
    torch=None; model=None; calls=[]; pipelines=[]; code=1
    def save():
        report['geracoes_concluidas']=len(calls); report['metricas_automaticas']=summarize(pipelines)
        training.atomic_json(directory/'relatorio.json',report)
        training.atomic_json(directory/('chamada_'+stamp+'.json'),report)
    def phase(name): report['etapa']=name; save(); print('08d: '+name,flush=True)
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
        report.update(estado='extracao08d_concluida_revisao_pendente',etapa='concluido',
            sha256_arquivos={n:sha256((directory/n).read_bytes()) for n in ('extracoes.jsonl','geracoes.jsonl')},
            aviso='Trechos e estrutura válidos não comprovam suporte semântico; nenhum modelo foi selecionado.')
        code=0
    except (Exception,KeyboardInterrupt) as exc:
        report.update(estado='extracao08d_interrompida',etapa_falha=report['etapa'],erro=dict(tipo=type(exc).__name__,mensagem=helper.safe_error_message(exc)))
    finally:
        if torch is not None and torch.cuda.is_available():
            try: report['memoria_final']=helper.memory_snapshot(torch)
            except Exception as exc: report['erro_medicao_memoria']=type(exc).__name__
        report['duracao_chamada_segundos']=round(time.perf_counter()-started,2)
        try: save()
        finally: lock.unlink(missing_ok=True)
        print('RESUMO DO 08d — copie este bloco',flush=True)
        print(json.dumps({k:report.get(k) for k in ('estado','geracoes_concluidas','metricas_automaticas','retomadas_do_drive','memoria_final','erro')},ensure_ascii=False,indent=2),flush=True)
        print('Relatório: '+str(directory/'relatorio.json'),flush=True)
    return code

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raiz',type=Path,required=True)
    parser.add_argument('--perfil',default='config/perfil_extracao_validacao2_v4.json')
    parser.add_argument('--validar_apenas',action='store_true')
    args=parser.parse_args(); root=args.raiz.resolve()
    if args.validar_apenas:
        profile=json.loads(training.safe_path(root,args.perfil).read_bytes()); material=preflight(root,profile)
        print(json.dumps(dict(estado='integridade_extracao_aprovada',familias=2,ids=[r['id_familia_docdb'] for r in material['records']],checkpoint=profile['checkpoint']['diretorio'])))
    else: raise SystemExit(run(root,args.perfil))

if __name__=='__main__': main()
