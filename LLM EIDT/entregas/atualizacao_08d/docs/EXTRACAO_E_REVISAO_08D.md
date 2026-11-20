# 08d — extração com as regras D1–D5

Versão 4.0, 15/11/2026. Preparação de experimento de desenvolvimento após revisão humana. Não é nova avaliação independente do artigo.

## O que muda

Somente as instruções de elementos e relações/efeitos são revisadas. Elas incorporam unidade técnica central; propriedades como atributos; exclusão de caracterização auxiliar de memes; operações explicitamente nomeadas; separação de materiais; preservação de alternativas e operadores; distinção entre finalidade e resultado alegado; e cautela com a origem documental desconhecida.

O código não força listas a coincidir com a referência e não corrige respostas. Não há termos bloqueados por patente, exemplos resolvidos, IDs de famílias nas instruções, contagens esperadas ou leitura da referência durante a geração. As regras foram desenvolvidas após observar estas famílias: mesmo sem incluir um gabarito no prompt, melhora nelas não prova generalização.

## O que permanece fixo

Mesmas famílias de validação do 08c: 68698300 e 50390156; mesma ordem. Mesmo Qwen3-8B/revisão, checkpoint da época 3, quantização NF4/FP16, schema, gramática, semente e geração greedy sem thinking. Até 3.072 tokens de entrada e 1.024 de saída por chamada, sem recorte. O máximo continua sendo oito chamadas: elementos e relações para duas famílias e duas variantes. Não há aumento de orçamento para favorecer esta revisão.

O segundo estágio recebe os elementos da própria variante; comparação é do fluxo completo. O núcleo do 08c é reutilizado sem edição e conferido por hash. Código de orquestração, perfil e pasta de resultados são novos. O perfil registra a assinatura da referência para análise posterior, mas o programa não abre esse arquivo. Esquemas/validação continuam técnicos; não passam a comprovar suporte semântico.

## Antes de abrir no Colab

1. Extraia entregas/atualizacao_08d.zip. Copie o CONTEÚDO para a pasta Replicação LLM EIDT IC no Drive, mesclando notebooks, scripts, config, prompts e docs. Substitua SHA256SUMS.txt pelo incluído. Não crie outra pasta de projeto dentro da atual.
2. Preserve o projeto anterior completo, especialmente scripts/perfis do 08/08b/08c, requirements_extracao08c.txt, dados processados e checkpoint do 05. O pacote contém a atualização e duas dependências congeladas do 08c, mas não leva os dados nem o adaptador do Drive.
3. Abra notebooks/08d_extrair_evidencias_regras.ipynb no Colab e selecione GPU. Confira PASTA_DRIVE na primeira célula se o projeto estiver em outro local/conta. Execute em ordem (Executar tudo).
4. Conferência de arquivos/checkpoint ocorre antes do carregamento. Em caso de arquivo de outra versão, atualize os arquivos indicados; não altere hashes para contornar a falha. Dependências são as mesmas do 08c; torch e NumPy nativos são preservados e inventariados. Não há atualização solicitada de bibliotecas ou retreinamento.

## Execução e retomada

Pesos no armazenamento temporário do Colab; primeiro download aproximadamente 16 GB. A memória precisa ser medida na GPU real: o aumento do tamanho das instruções pode aumentar custo de entrada apesar dos limites iguais. Não garantimos o mesmo tempo/memória do 08c.

Resultados em resultados/etapa_5d/piloto_br_200/extracao_<hash-do-perfil>/. Cada chamada salva saída bruta, tokens, prompt/schema e validação. Chamada concluída inválida não é refeita automaticamente. Se elementos falham, relações ficam bloqueadas. Saídas rejeitadas não viram ausência de evidência. Queda antes de salvar pode exigir repetir apenas a chamada não persistida.

Não usar duas sessões ao mesmo tempo. Liberar trava residual somente após encerrar a anterior. Retomada exige o mesmo perfil, código e ambiente inventariado; divergências interrompem. Não apagar tentativas para escolher a melhor resposta. GPU/versões diferentes devem ser registradas como condição diferente, nunca disfarçadas de retomada equivalente.

## Análise prevista, antes de ver os novos resultados

Primeiro relatar chamadas previstas/concluídas, término/truncamento/repetição, validade por etapa, fluxos completos e memória. Depois confrontar os seis grupos com a referência consolidada v2 e os textos, usando mapeamento um a um sem fusão corretiva. Preservar alvo, operadores e alternativa conjunta; separar categorias materiais; não creditar custo/eficiência sem suporte. Não converter validade de JSON em precisão.

Usar a referência v2 congelada para a comparação principal de desenvolvimento com 08c. As ressalvas de cobertura de memes (substrato e seleção) continuam explícitas; qualquer revisão adicional da referência terá versão separada e deverá reavaliar ambas as versões, sem favorecer 08d. Métricas permanecem condicionais, com falhas no denominador, e não justificam escolher modelo para produção só por dois casos. Um anotador exposto mais assistência de IA não equivale a dois avaliadores independentes.

Os formulários auxiliares produzidos pelo núcleo histórico não substituem a referência v2. Seu nome “anotacao_independente” não torna esta revisão independente. Não preencher nem alterar a referência para fazer coincidir com 08d. Enviar relatorio.json, geracoes.jsonl e extracoes.jsonl e o resumo final. Preservar a pasta inteira, inclusive prompts, trechos, respostas e preparação do ambiente.

Depois de examinar o resultado, decidir se cabe avaliar em outras famílias de validação com referência anotada antes das previsões. As 20 famílias de teste não são usadas para ajustar instruções. Não executar alinhamento nem ampliar às 200 com base só no sucesso técnico.

## Verificação da entrega

A validação local deve constar em VALIDACAO_ENTREGA_08D.md: seleção/configuração, limites com tokenizador real, gramática e persistência/retomada simuladas. GPU, modelo completo NF4 e qualidade de extração no 08d serão medidos pelo pesquisador no Colab; não são declarados testados localmente.
