# LLM-EIDT — piloto brasileiro PATSTAT, 200 famílias

Protocolo 3.0, registrado em 3 de novembro de 2026. Este projeto adapta o método do artigo ao contexto brasileiro, utilizando uma extração PATSTAT já existente e autorizada pelo pesquisador. A configuração ativa está em `config/experimento.json`; a definição metodológica completa está em `docs/ADAPTACAO_METODOLOGICA_BR.md`.

## Base e amostra congelada

- Fonte: PATSTAT Global/EPO TIP, pacote de 1.000 famílias DOCDB com vínculo BR, depósitos de 2010–2024.
- Recorte atual: qualquer CPC da família começando com A61 ou C12N. A consulta antiga também incluía IPC C12Q; como o pacote não exporta IPC, o filtro atual utiliza os CPCs disponíveis.
- Elegíveis: 960 famílias. Piloto: 200 famílias, 160 de treino, 20 de validação e 20 de teste; janelas de 67/67/66 famílias e semente 42.
- Divisões originais preservadas. Português e inglês aceitos por campo, inclusive título/resumo em idiomas diferentes.
- Qwen3-8B + LoRA planejado para adaptação ao CPC proxy e extração. E5 multilíngue planejado para alinhamento.

O ZIP original, a amostra de 200 e os arquivos pré-processados estão incluídos. Reexecutar os notebooks reproduz os arquivos e verifica sua integridade; divergências interrompem a execução para revisão.

## Próximos passos no Colab

1. Envie os arquivos desta pasta atualizada para `Meu Drive/Replicação LLM EIDT IC`, preservando as subpastas. Aceite a atualização dos arquivos correspondentes. Os relatórios antigos de GPU podem continuar guardados no Drive.
2. Abra `notebooks/00_preparar_drive_e_auditar_insumos.ipynb` em CPU e execute as células. Monte o Drive, confira a pasta e a auditoria dos insumos. Anotação humana e rede de citações continuam pendentes; isso não impede a preparação do piloto.
3. Execute `notebooks/02_selecionar_200_patstat_br.ipynb` em CPU. O resultado esperado é 960 elegíveis, 200 selecionadas e 160/20/20 nas partições. O notebook confere o pacote, as famílias e a amostra.
4. Execute `notebooks/03_preprocessar_patstat_br.ipynb` em CPU. Ele instala somente o validador de JSON necessário, prepara entradas pt/en e separa os alvos CPC. O modelo ainda não é carregado.
5. Confira os relatórios de seleção e pré-processamento. Antes de iniciar treinamento real, resolva o perfil de GPU e o plano de avaliação CPC/extração.

O notebook `01_validar_gpu_e_modelos.ipynb` foi atualizado para este perfil. A versão anterior já testou sua infraestrutura; os relatórios antigos continuam úteis. Ele pode ser repetido se o ambiente mudar, mas aprovação do diagnóstico não garante capacidade para treinar o modelo inteiro.

A sessão informada tinha 14,46 GiB de VRAM livre e não oferecia BF16 nativo. O perfil LoRA BF16 atual não é viável nessa GPU. Ele mantém microbatch 1, acumulação 16, contexto 2.048, rank 8 e módulos `q_proj`/`v_proj`. O teste QLoRA 4-bit agora possui um perfil adicional, com registro próprio, descrito na seção final deste documento.

O antigo `02_registrar_coleta_e_selecionar_200.ipynb` passa a ser um aviso de substituição. Use o novo notebook 02 PATSTAT. Os antigos manifestos e o seletor chinês podem existir como legado e não são usados pelos notebooks ativos. O notebook da consulta PATSTAT em `dados/referencia/` é documentação de origem, não um passo a executar neste piloto.

## Organização dos arquivos

| Caminho | Conteúdo |
|---|---|
| `config/experimento.json` | Modelo, dados, estratos, parâmetros e lacunas |
| `config/insumos_patstat_br_200.csv` | Manifesto editável do novo piloto |
| `dados/brutos/patstat_br_1000/` | ZIP congelado e registro de proveniência |
| `dados/processados/piloto_br_200/` | Amostra de 200 e auditoria |
| `dados/processados/piloto_br_200/preprocessado/` | Entradas, metadados, supervisão CPC e auditoria |
| `schemas/extracao_patstat_br.schema.json` | Contrato JSON da resposta do extrator |
| `prompts/extracao_patstat_br.txt` | Instruções de extração pt/en com evidências |
| `scripts/selecionar_piloto_br.py` | Seleção reproduzível por família/estrato |
| `scripts/preprocessar_patstat_br.py` | Preparação dos dados e validação de extrações |
| `resultados/etapa_1/piloto_br_200/` | Relatórios produzidos no Colab |
| `docs/` | Auditoria metodológica e validação da entrega |

`SHA256SUMS.txt` identifica os arquivos fixos da entrega. O manifesto editável e os relatórios gerados durante a execução ficam fora desse índice. Não edite amostras congeladas para contornar uma falha de hash; investigue a divergência e registre outra versão quando houver uma mudança intencional de protocolo.

## Interpretação científica

Os dados representam famílias com vínculo brasileiro, não necessariamente pedidos representantes brasileiros. O título e o resumo podem ter sido escolhidos em membros diferentes da família. A origem de cada texto, datas de publicação, edição PATSTAT e data da extração não foram conservadas no pacote.

O alvo `cpc_proxy` é o primeiro código CPC integral em ordem alfanumérica, herdado da extração; não é classificação principal oficial nem ouro humano. Apenas 3/20 rótulos de validação e 3/20 de teste aparecem no treino. Essa dispersão deve orientar o plano de avaliação antes de ajustar o modelo.

A preparação pt/en preserva evidências literais e não traduz previamente os textos. A futura extração será avaliada em seis grupos: memes, convergências, funções, materiais, processos e efeitos. JSON válido, por si só, não comprova evidência correta.

As 200 famílias permitem um piloto exploratório. Histórico anterior a 2010, citações e anotação independente ainda são necessários para as análises correspondentes. Nesta entrega não foram executados treinamento real, extração por LLM, embeddings, alinhamento ou indicadores bibliométricos.

## Após a conferência dos notebooks 02 e 03

Os relatórios enviados pelo pesquisador foram conferidos: 200 famílias, 160/20/20 e cinco hashes de arquivos pré-processados iguais à entrega local. O diagnóstico 01 confirmou que a sessão disponível não comporta o perfil BF16.

O próximo notebook é **04_testar_qlora_gpu.ipynb**, em GPU. Ele utiliza um perfil adicional em `config/perfil_qlora_teste.json` para carregar Qwen3-8B em NF4 de 4 bits, calcular em FP16 e executar um único passo de diagnóstico com LoRA. O `experimento.json` e a amostra congelada continuam vinculados aos hashes dos resultados 02/03.

Atualize no Drive os arquivos desta entrega, incluindo o índice `SHA256SUMS.txt`, e execute o 04. Não é necessário repetir 00/02/03 para iniciar esse teste após conferir a atualização. O relatório ficará em `resultados/etapa_1/piloto_br_200/qlora_teste_<UTC>.json`. A metodologia e as limitações estão em `docs/TESTE_QLORA_GPU.md`. O teste não salva um adaptador para avaliação; treinamento completo permanece como etapa posterior.

## Revisão do teste após falta de memória

A execução no Colab do teste QLoRA com 2.048 posições falhou por falta de memória na fase de treinamento. O notebook04 atualizado usa agora `config/perfil_qlora_teste_1024.json`, com limite de 1.024 posições. Os 160 exemplos de treino têm até 744 tokens e continuam completos. A mudança é registrada em `docs/AJUSTE_QLORA_1024.md`; a configuração anterior continua disponível para rastreabilidade.

Atualize no Drive o notebook04, `scripts/testar_qlora_gpu.py`, o novo perfil1024 e `SHA256SUMS.txt`. Abra a versão atualizada do04 na sessão GPU e execute suas células. Preserve o cache da sessão existente quando possível. O relatório distingue agora carregamento, forward, backward e passo do otimizador. Reduzir o contexto visa reduzir memória; o resultado real continua dependente da execução no Colab.
