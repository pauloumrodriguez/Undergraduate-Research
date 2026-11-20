# 08d-validacao4 — instruções D1–D5 congeladas em quatro famílias novas

Versão 4.0-val4, 19/11/2026. Desenvolvimento/validação exploratória. Não é teste independente nem avaliação de generalização.

## O que muda em relação ao 08d

Só a amostra, o orçamento e a pasta de resultados:

- Famílias: 45975308, 65439381, 74045448, 80949080 (nessa ordem). São as quatro restantes das seis do 08b, após retirar 68698300 e 50390156.
- Orçamento: no máximo 16 chamadas (4 famílias × base/adaptado × elementos/relações). Orçamento por chamada igual ao 08d: 3.072 tokens de entrada, 1.024 de saída, sem recorte.
- Resultados em `resultados/etapa_5e/piloto_br_200/extracao_<hash-do-perfil>/` (o 08d permanece em `etapa_5d`).

## O que permanece fixo (verificado por hash no preflight)

Prompts v4 de elementos e relações, regras D1–D5, schemas, gramática, Qwen3-8B/revisão, checkpoint (época 3, passo 30), NF4/FP16, semente 42, geração greedy sem thinking, dependências, núcleo 08c (v3) e script 08d (v4), ambos importados sem edição. Alterar qualquer um interrompe a execução. A referência v3 não é aberta pelo programa.

## Critérios definidos antes de ver os resultados

1. Relatar primeiro: chamadas previstas/concluídas, término/truncamento/repetição, validade por etapa, fluxos completos, memória e tempo. Falhas ficam no denominador; não viram ausência de evidência.
2. Depois comparar os seis grupos com a referência v3 por mapeamento um a um, sem fusão corretiva, preservando operadores e alternativas conjuntas. Resultados por família e agregados, com e sem as duas famílias de desenvolvimento; a leitura principal de "fora do desenvolvimento" usa só as quatro novas.
3. Pares de convergência: a referência não tem pares positivos. Qualquer par proposto pelo modelo é falso positivo condicional; reportar contagem, sem calcular F1 de pares.
4. Não escolher variante de produção (base × adaptado) por quatro famílias. Registrar a evidência e o critério antes de novos dados.
5. Não alterar prompts, regras ou referência depois de ver os resultados. Se isso for necessário, será uma nova versão com nova rodada.
6. As 20 famílias de teste não são usadas. Não avançar a alinhamento ou às 200 famílias apenas por sucesso técnico.

## Como executar

1. Extraia `entregas/atualizacao_08d_validacao4.zip` e copie o conteúdo para a pasta do projeto no Drive, mesclando subpastas e substituindo `SHA256SUMS.txt`. Preserve dados, checkpoint e scripts anteriores.
2. Abra `notebooks/08d_extrair_evidencias_validacao4.ipynb` no Colab com GPU T4 e execute em ordem.
3. Envie `relatorio.json`, `extracoes.jsonl`, `geracoes.jsonl` e o resumo final. Preserve a pasta inteira. Não apague tentativas inválidas.

Tempo e memória de GPU não foram medidos localmente; o 08d com duas famílias serve só de referência de ordem de grandeza. A família mais longa tem 1.313 caracteres, abaixo dos 1.984 da maior família do 08d (2.581 tokens de entrada medidos lá), mas isso é estimativa por comprimento, não medição com o tokenizador.

## Limites

Um anotador; exposição prévia às previsões de 08/08b; regras nascidas de outras duas famílias; sem pares positivos na referência. Ver `PROTOCOLO_REFERENCIA_V3.md`.
