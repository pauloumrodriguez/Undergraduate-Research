# LLM-EIDT — piloto brasileiro PATSTAT, 200 famílias

Adaptação do estudo ao contexto brasileiro: famílias com vínculo BR, depósitos de 2010–2024 e recorte CPC A61 ou C12N disponível no pacote PATSTAT. O piloto preserva 160 famílias de treino, 20 de validação e 20 de teste. Metodologia e limitações: `docs/ADAPTACAO_METODOLOGICA_BR.md`.

## Estado atual

O notebook 05 concluiu no Colab três épocas e 30 atualizações com Qwen3-8B QLoRA NF4/FP16. A época 3 foi selecionada pela perda de validação, que passou de 4,373849 antes do ajuste para 0,600219. Os dois relatórios enviados pelo pesquisador foram conferidos com os arquivos locais e arquivados em `resultados/etapa_2/piloto_br_200/`. A partição teste permanece reservada. A redução da perda por token ainda precisa ser confrontada com os códigos gerados livremente.

## Próximo passo: notebook 06 em GPU

O notebook **`notebooks/06_avaliar_cpc_validacao.ipynb`** compara o modelo base e o adaptador selecionado nas 20 famílias de validação: 40 gerações ao todo. Ele verifica o checkpoint no Drive, usa o mesmo prompt sem fornecer o alvo CPC e registra acerto do código completo, formato sintático e comparação pareada. Não treina nem abre o arquivo de teste.

Atualize no Drive estes quatro arquivos, preservando as subpastas dentro de `Meu Drive/Replicação LLM EIDT IC`:

- `notebooks/06_avaliar_cpc_validacao.ipynb`
- `scripts/avaliar_cpc_geracao.py`
- `config/perfil_avaliacao_cpc_validacao.json`
- `SHA256SUMS.txt`

O notebook utiliza os helpers `scripts/testar_qlora_gpu.py` e `scripts/treinar_qlora_cpc.py` já instalados com o 05. Preserve os requisitos, dados, relatórios e a pasta inteira do checkpoint no Drive. O caminho do resultado aprovado do 05 está fixado no perfil do 06; não é preciso escolher novamente a época nem copiar pesos para o computador.

Abra o 06 no Colab com GPU e execute as células em ordem. Não precisa repetir 00–05. Ao terminar, envie o bloco **RESUMO DA AVALIAÇÃO**, o relatório JSON e a tabela comparativa CSV indicados na saída. Se ocorrer falha, envie o resumo e o erro; as respostas parciais ficam registradas e não são apresentadas como avaliação completa.

## Fluxo do projeto

| Etapa | Estado e finalidade |
|---|---|
| 00, 02, 03 | Preparação, seleção e textos pt/en concluídos |
| 01 e 04b | Diagnóstico de GPU e teste QLoRA concluídos |
| 05 | Treinamento CPC concluído; checkpoint da época 3 selecionado |
| 06 | Entregue para comparação por geração nas 20 validações |
| 07 | A preparar: avaliação final CPC nas 20 famílias de teste, após congelar o procedimento |
| 08 | A preparar: extração estruturada, evidências e validação humana |
| 09 | A preparar: embeddings E5 e alinhamento dos elementos extraídos |
| 10 | A preparar: redes, indicadores e análise científica dos limites do piloto |

O protocolo do 06 e a sequência detalhada estão em `docs/AVALIACAO_CPC_E_PROXIMAS_ETAPAS.md`. A verificação local do notebook está documentada em `docs/VALIDACAO_ENTREGA_06.md`. As etapas 07–10 são planejamento, não arquivos executáveis já entregues.

## Rastreabilidade e limites

`config/experimento.json` e os dados preparados permanecem congelados. Perfis adicionais registram as escolhas computacionais e de avaliação. Resultados do 06 vão para `resultados/etapa_3/piloto_br_200/`. O índice `SHA256SUMS.txt` identifica os arquivos fixos da entrega, incluindo as cópias dos dois relatórios 05 incorporadas nesta versão; novos resultados de execução não entram automaticamente nesse índice. Não edite hashes para contornar uma divergência.

O CPC proxy não é classificação principal oficial nem anotação de extração. A validação já escolheu a época, por isso a comparação do 06 é diagnóstica. Nenhuma taxa de acerto CPC demonstra, por si só, a qualidade dos seis campos de extração.

Os textos podem vir de membros diferentes da família, e o pacote não conserva a origem de cada título/resumo, edição PATSTAT, data da extração, citações ou datas de publicação. As métricas que dependem desses insumos exigem dados adicionais ou uma delimitação explícita da análise exploratória. O piloto brasileiro não reproduz automaticamente os resultados numéricos do corpus chinês.
