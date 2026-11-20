# Notebook 07 — avaliação final CPC

Protocolo congelado em 5 de novembro de 2026, antes de usar as respostas do teste. O objetivo é comparar Qwen3-8B base e adaptador da época 3 nas 20 famílias de teste do piloto brasileiro.

## O que permanece fixo

O 07 importa diretamente do programa 06 as funções de prompt, geração, normalização, pontuação, agregação e exportação CSV. Mantém a revisão do modelo, NF4/FP16, checkpoint passo 30, uma família por vez, entrada de até 992 tokens, até 32 tokens novos, geração greedy, EOS e métricas. O alvo CPC não entra no prompt. Não há treinamento ou nova seleção de época.

As mudanças são a partição `teste`, o perfil e os caminhos de saída. O arquivo de entrada é vinculado ao hash registrado na auditoria de pré-processamento. O procedimento e o checkpoint são conferidos com o perfil e o relatório reais do 06 antes de abrir essa partição. O histórico de seleção continua usando a perda de validação do 05.

Métrica primária: acerto exato do CPC proxy integral, após NFC, maiúsculas e remoção de espaços, com resposta encerrada em EOS. Denominador fixo de 20 famílias por variante; saídas inválidas permanecem no denominador. Métricas secundárias: formato sintático compatível, terminação, limite atingido e comparação pareada. Não são acrescentadas métricas hierárquicas depois de observar os resultados.

## Execução

Atualizar no Drive o notebook `07_avaliar_cpc_teste.ipynb`, `scripts/avaliar_cpc_teste.py`, `config/perfil_avaliacao_cpc_teste.json` e `SHA256SUMS.txt`. Os arquivos do 06, o checkpoint do 05, os relatórios e os dados preparados já devem permanecer no Drive.

Abrir o 07 no Colab com GPU e executar em ordem. A conferência inicial já abre o arquivo de teste para validação, após verificar o protocolo congelado; a geração acontece na célula final de execução. São 40 respostas: base e adaptador para cada uma das mesmas 20 famílias. Não é necessário repetir os notebooks anteriores.

Resultados em `resultados/etapa_4/piloto_br_200/avaliacao_cpc_<datahora>/`: `relatorio.json`, `comparacao_cpc.csv`, `predicoes_cpc.jsonl` e prompts auditados. O notebook também salva um relatório de chamada e outro de preparação. Ao terminar, enviar o resumo do teste, o relatório JSON e o CSV. Preservar a pasta completa.

Se houver interrupção ou erro, manter o relatório e as saídas parciais. Corrigir somente falhas demonstráveis e registrar o motivo de uma nova execução. Não selecionar a melhor execução nem alterar parâmetros depois de ver os resultados. Qualquer estudo de otimização posterior precisa de um novo protocolo de avaliação.

## Verificação local e limites

Cinco testes de software passaram usando uma partição sintética: aceitação da coorte correta, bloqueio de mudanças no procedimento antes da leitura do teste, rejeição de hash divergente, rejeição de famílias sobrepostas à validação e relatório de erro sem métricas finais. O notebook foi compilado e suas células estão sem saídas antigas. As funções científicas são as mesmas já testadas e executadas pelo 06.

O conteúdo das famílias reais de teste não foi usado para desenvolver ou selecionar parâmetros do 07. Não houve inferência GPU local; o checkpoint real será verificado e carregado no Colab. A conferência de instalação calcula hashes dos arquivos congelados, sem usar seus textos/rótulos para analisar desempenho.

O resultado é uma avaliação do CPC proxy no piloto de 200 famílias, com apenas 20 famílias no teste; não demonstra sozinho qualidade da extração dos seis grupos do artigo. Depois da análise do 07, o próximo trabalho será extração estruturada com evidências e validação humana, comparando base e adaptador.
