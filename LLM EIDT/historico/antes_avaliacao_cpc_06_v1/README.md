# LLM-EIDT — piloto brasileiro PATSTAT, 200 famílias

Adaptação metodológica para famílias com vínculo brasileiro, depósitos de 2010–2024 e recorte CPC disponível A61 ou C12N. A extração PATSTAT original continha 1.000 famílias; 960 são elegíveis no recorte atual e 200 foram selecionadas, preservando as partições originais. Detalhes e limitações: `docs/ADAPTACAO_METODOLOGICA_BR.md`.

## Estado atual e próximo notebook

Os notebooks 02 e 03 concluíram seleção e pré-processamento: **160 famílias de treino, 20 de validação e 20 de teste**. O pesquisador informou aprovação do teste 04b com Qwen3-8B em NF4/FP16, contexto 1.024, pico alocado 11,768 GiB e pico reservado 12,605 GiB. A perda de um único passo não comprova qualidade do modelo.

O próximo notebook é **`notebooks/05_treinar_qlora_cpc.ipynb`**, com GPU no Colab. Ele treina por três épocas nas 160 famílias e seleciona o adaptador pela perda das 20 famílias de validação. As 20 de teste permanecem reservadas. O treinamento completo ainda precisa ser executado no Colab. Protocolo: `docs/TREINAMENTO_QLORA_CPC.md`.

Para esta atualização, copie para as subpastas correspondentes em `Meu Drive/Replicação LLM EIDT IC`:

- `notebooks/05_treinar_qlora_cpc.ipynb`
- `scripts/treinar_qlora_cpc.py`
- `scripts/testar_qlora_gpu.py` (dependência compartilhada, mesma versão do 04b aprovado)
- `config/perfil_treino_qlora_1024.json`
- `SHA256SUMS.txt`

Também atualize este README, a documentação e os relatórios de validação locais para manter o registro completo. Preserve os relatórios produzidos pelo Colab. Abrir só o notebook não atualiza os programas nem as configurações no Drive.

No 05, deixar `RETOMAR_CHECKPOINT` vazio na primeira execução, conferir a pasta e executar as células em ordem. O caminho do relatório 04b aprovado já vem preenchido. Não é preciso repetir os notebooks anteriores. Checkpoints no Drive permitem retomar uma sessão interrompida; use o caminho do último checkpoint completo no campo `RETOMAR_CHECKPOINT`.

## Fluxo completo

| Notebook | Ambiente | Função |
|---|---|---|
| 00 | CPU | Montagem do Drive e auditoria dos insumos |
| 02_selecionar_200_patstat_br | CPU | Seleção reproduzível das 200 famílias |
| 03_preprocessar_patstat_br | CPU | Entradas pt/en e separação dos alvos CPC |
| 01 | GPU | Diagnóstico do ambiente; BF16 inviável na sessão informada |
| 04b_testar_qlora_1024 | GPU | Um passo QLoRA de capacidade; aprovado conforme resumo enviado |
| 05_treinar_qlora_cpc | GPU | Treinamento CPC, validação e salvamento dos adaptadores |

O antigo 02 de coleta chinesa é legado. O 04 original/variante 2.048 e os registros de falha permanecem para rastreabilidade. Use 04b para identificar o diagnóstico de 1.024 posições. Os relatórios antigos não precisam ser removidos.

## Configuração e arquivos

`config/experimento.json` preserva o protocolo base e os hashes dos dados preparados. `config/perfil_treino_qlora_1024.json` registra as escolhas desta execução: Qwen3-8B fixado por revisão, quantização NF4, cálculo FP16, LoRA rank 8 em q/v, contexto 1.024, microbatch 1, acumulação 16, três épocas e taxa constante 0,0003. Isso é uma variante computacional explicitamente documentada do estudo original.

Os dados congelados ficam em `dados/processados/piloto_br_200/`. Resultados anteriores estão em `resultados/etapa_1/piloto_br_200/`; treinamento e checkpoints ficam em `resultados/etapa_2/piloto_br_200/`. O arquivo `SHA256SUMS.txt` indexa os arquivos fixos da entrega. Manifestos editáveis e novos resultados de execução não pertencem automaticamente ao índice. Não modificar amostras nem hashes para contornar uma divergência.

## Limites científicos

O alvo CPC é um proxy alfanumérico da família, não um código principal oficial nem ouro humano. Há 142 códigos distintos no treino e 17 das 20 famílias de validação possuem código integral ausente no treino. O notebook 05 seleciona pela perda de tokens CPC, sem alegar acurácia ou melhoria da extração.

Os textos podem vir de membros diferentes da família; o pacote não registrou o identificador de origem de cada título/resumo, edição PATSTAT, data da extração, citações ou datas de publicação. Português/inglês são preservados sem tradução. Os seis grupos de extração, o alinhamento por E5 e os indicadores de novidade ainda exigem implementação/validação, inclusive anotação independente e dados históricos/citações quando aplicáveis.
