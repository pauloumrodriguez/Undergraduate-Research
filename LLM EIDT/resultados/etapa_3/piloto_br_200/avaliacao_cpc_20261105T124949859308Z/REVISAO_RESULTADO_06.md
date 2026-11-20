# Revisão do resultado do notebook 06

Data: 5 de novembro de 2026. Execução: `avaliacao_cpc_20261105T124949859308Z`.

## Evidências conferidas

- Relatório concluído, sem erro: 40 gerações, duas variantes nas mesmas 20 famílias de validação.
- CSV confere com o SHA-256 registrado no relatório. Contagens de acerto e formato foram recalculadas; código, perfil e oito fontes correspondem à entrega local.
- Base: 0/20 acertos integrais e 1/20 respostas em formato sintático compatível.
- Adaptador da época 3: 1/20 acertos integrais e 20/20 respostas em formato sintático compatível.
- Todas as 40 respostas encerraram em EOS; nenhuma atingiu o limite de geração. O relatório informa ausência de recorte e contexto máximo de 688 tokens de entrada.
- As 20 previsões do adaptador são distintas. Não se observou repetição de uma única classe neste conjunto.
- 17 dos 20 alvos integrais de validação não constam no treino. O único acerto, família 44484027 / A61F13/08, também corresponde a um alvo ausente no treino.
- O arquivo da partição teste não foi aberto nesta revisão. Arquivos brutos de tokens/prompts do Colab não foram recebidos; esta conferência cobre os dois arquivos enviados, o programa local e sua proveniência.

## Interpretação

A melhoria mais clara foi a conformidade de formato. O ganho de um acerto em 20 exemplos não estabelece melhoria robusta de classificação ou generalização. A queda de perda por token no treino/validação não equivale ao acerto do símbolo CPC completo. A raridade dos alvos e sua natureza de proxy alfanumérico da família limitam a interpretação, mas não justificam reclassificar respostas incorretas como acertos.

Não foi identificado defeito de contagem ou integridade nos arquivos conferidos que exija repetir o 05 ou o 06. A qualidade da extração dos seis grupos do artigo permanece desconhecida e deve ser avaliada diretamente, comparando base e adaptador.

## Decisão para o próximo passo

Preservar este resultado como diagnóstico de validação. Preparar o notebook 07 para a avaliação final nas 20 famílias de teste, mantendo a revisão Qwen3-8B, NF4/FP16, checkpoint da época 3, prompt, geração greedy, limite de 32 tokens, normalização, exigência de EOS e critério de acerto integral do 06. Mudar somente a partição avaliada e os caminhos de resultados, em um novo perfil com hashes próprios.

Antes da execução, conferir seleção do checkpoint e congelar os arquivos de avaliação. Após abrir o teste, não ajustar época, seed, prompt ou parser a partir de seus resultados. Qualquer otimização futura será outro experimento documentado, com nova estratégia de avaliação; os resultados atuais não serão substituídos.

Depois do teste CPC, prosseguir à extração estruturada e à revisão humana das evidências. A baixa acurácia CPC não demonstra, por si só, fracasso ou sucesso nessa tarefa diferente.
