# LLM-EIDT — piloto brasileiro PATSTAT, 200 famílias

Adaptação do estudo ao contexto brasileiro: famílias com vínculo BR, depósitos de 2010–2024 e recorte CPC A61 ou C12N disponível no pacote PATSTAT. O piloto preserva 160 famílias de treino, 20 de validação e 20 de teste. Metodologia e limitações: `docs/ADAPTACAO_METODOLOGICA_BR.md`.

## Estado atual

O notebook 05 concluiu no Colab três épocas e 30 atualizações com Qwen3-8B QLoRA NF4/FP16. A época 3 foi selecionada pela perda de validação, que passou de 4,373849 antes do ajuste para 0,600219. Os dois relatórios enviados pelo pesquisador foram conferidos com os arquivos locais e arquivados em `resultados/etapa_2/piloto_br_200/`. A partição teste permanece reservada. A redução da perda por token ainda precisa ser confrontada com os códigos gerados livremente.

## Próximo passo: notebook 07 em GPU

O 06 concluiu as 40 gerações nas 20 famílias de validação: a base acertou 0/20 códigos e o adaptador 1/20. O formato sintático foi compatível em 1/20 e 20/20, respectivamente. O diagnóstico foi registrado sem alterar o treinamento ou o procedimento de avaliação.

O próximo notebook é `notebooks/07_avaliar_cpc_teste.ipynb`, para avaliar nas 20 famílias de teste com o procedimento congelado do 06. Atualize no Drive o notebook 07, `scripts/avaliar_cpc_teste.py`, `config/perfil_avaliacao_cpc_teste.json` e `SHA256SUMS.txt`, preservando as subpastas. Mantenha os arquivos do 06, relatórios e checkpoint do 05.

Abra o 07 com GPU e execute em ordem. Não é preciso repetir etapas anteriores. Envie o resumo do teste e os arquivos `relatorio.json` e `comparacao_cpc.csv` da nova pasta em `resultados/etapa_4/piloto_br_200/`. Não ajuste parâmetros nem selecione execuções pelos resultados de teste.

Detalhes e verificação local: `docs/AVALIACAO_FINAL_CPC_07.md`.

## Fluxo do projeto

| Etapa | Estado e finalidade |
|---|---|
| 00, 02, 03 | Preparação, seleção e textos pt/en concluídos |
| 01 e 04b | Diagnóstico de GPU e teste QLoRA concluídos |
| 05 | Treinamento CPC concluído; checkpoint da época 3 selecionado |
| 06 | Concluído e revisado nas 20 famílias de validação |
| 07 | Entregue para avaliação final CPC nas 20 famílias de teste |
| 08 | A preparar: extração estruturada, evidências e validação humana |
| 09 | A preparar: embeddings E5 e alinhamento dos elementos extraídos |
| 10 | A preparar: redes, indicadores e análise científica dos limites do piloto |

O protocolo do 06 e a sequência detalhada estão em `docs/AVALIACAO_CPC_E_PROXIMAS_ETAPAS.md`. A verificação local do notebook está documentada em `docs/VALIDACAO_ENTREGA_06.md`. As etapas 08–10 são planejamento, não arquivos executáveis já entregues.

## Rastreabilidade e limites

`config/experimento.json` e os dados preparados permanecem congelados. Perfis adicionais registram as escolhas computacionais e de avaliação. Resultados do 06 vão para `resultados/etapa_3/piloto_br_200/`. O índice `SHA256SUMS.txt` identifica os arquivos fixos da entrega, incluindo as cópias dos dois relatórios 05 incorporadas nesta versão; novos resultados de execução não entram automaticamente nesse índice. Não edite hashes para contornar uma divergência.

O CPC proxy não é classificação principal oficial nem anotação de extração. A validação já escolheu a época, por isso a comparação do 06 é diagnóstica. Nenhuma taxa de acerto CPC demonstra, por si só, a qualidade dos seis campos de extração.

Os textos podem vir de membros diferentes da família, e o pacote não conserva a origem de cada título/resumo, edição PATSTAT, data da extração, citações ou datas de publicação. As métricas que dependem desses insumos exigem dados adicionais ou uma delimitação explícita da análise exploratória. O piloto brasileiro não reproduz automaticamente os resultados numéricos do corpus chinês.
