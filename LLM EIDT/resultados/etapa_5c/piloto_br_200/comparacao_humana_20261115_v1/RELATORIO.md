# Comparação assistida da revisão humana com o 08c

15/11/2026 · duas famílias de validação · nenhuma execução de GPU

## Resultado

A revisão preenchida foi preservada integralmente. Suas 13 citações têm localização literal e posições corretas. A comparação cobre os 9 itens humanos, os 40 itens dos dois fluxos completos do adaptador e, separadamente, 16 itens da base na família curta (10 de elementos válidos como etapa e 6 da resposta de relações rejeitada). O JSON truncado da base na família longa não foi reparado nem transformado em itens aceitos.

**A estrutura melhorou; a qualidade semântica ainda não está aprovada.** O adaptador completou 2/2 fluxos e a base 0/2. Isso é cobertura técnica, não acurácia de extração ou prova de superioridade do LoRA.

## Achados principais

- Há correspondências diretas propostas no adaptado: derivado do esqueleto de organismo marinho como meme e seleção do substrato como processo. Elas são julgamentos assistidos, ainda não adjudicados.
- A família curta tem prevenção/tratamento divididos no modelo e reunidos na referência. A alegação de efeito terapêutico é parcialmente recuperada, com problemas de escopo e vínculos.
- No adaptado, “doenças” como material e “divulgação” como processo são erros de categoria. O material da família curta não é recuperado corretamente nesse grupo.
- Redução de custos e ganhos de eficiência foram afirmados sem suporte explícito. O fato de a citação existir não sustenta a interpretação. A base também faz uma alegação indevida de eficiência na resposta rejeitada.
- Os 12 pares do adaptado confundem relações parte–todo, representação, alternativas, propriedades e medição com convergência. A regra existente exige integração técnica, não simples relação ou coocorrência. Os julgamentos individuais estão no anexo.
- A função de crescimento/restauração do título da família longa não foi recuperada no grupo funções do adaptado. Sua menção em um efeito incorreto não recupera esse item na avaliação por campo.
- A referência humana também pode estar incompleta: determinação da absorção específica e medição da rugosidade estão explicitadas e aparecem no modelo, mas não foram anotadas. Não é correto marcá-las automaticamente como falsos positivos. Conversão de substrato está nomeada no título e merece avaliação separada da seleção.

## O que ainda impede métricas finais

Termos genéricos versus memes centrais, propriedades versus tecnologias, função versus efeito e granularidade das alternativas ainda exigem decisão. O material-base e o substrato constituído por ele não são equivalentes automaticamente. Há correspondências parciais e muitos-para-um, que não podem receber múltiplo crédito na pontuação.

A anotação é humana, mas posterior à exposição às previsões/comentários e com orientação do assistente. Não é referência independente, avaliação cega nem consenso entre avaliadores. Esta inspeção assistida não substitui segundo anotador ou adjudicador. Com duas famílias escolhidas por extremos de comprimento, não se estima desempenho no conjunto de 200 ou no universo brasileiro.

Precisão, revocação e F1 permanecem nulos, não zero. Nenhum percentual de acerto foi inferido do formato. Quando a referência for consolidada, o fluxo estrito deve manter as duas falhas da base no denominador: não excluir exemplos difíceis; itens humanos não recuperados permanecem falhas de cobertura. Uma análise parcial da base deve ser apresentada separadamente, nunca como extração final válida.

## Próxima ação concreta

Leia DECISOES_PARA_CONSOLIDAR.md. São cinco propostas para decidir sem preencher novamente toda a ficha. Responda com D1 a D5, indicando concordância ou ajustes; idealmente discutir com orientador/segundo anotador. A decisão humana será registrada em nova versão, mantendo o original.

Após essas decisões: consolidar referência de desenvolvimento e correspondências, produzir contagens justificadas e então avaliar se há correção demonstrável do protocolo. Não rodar 08c de novo, não treinar outro adaptador e não ampliar para 200 agora. Prompts, modelos, dados, checkpoint e notebooks não foram alterados. Não há notebook novo nesta entrega.

## Rastreabilidade e arquivos

- RELATORIO.html: este resumo, as decisões e todos os itens, com evidências e referência humana associada.
- comparacao_detalhada.json: 56 julgamentos assistidos individualizados, cobertura dos 9 itens humanos, falhas e hashes.
- decisoes_pendentes.json: propostas sem preenchimento de decisão humana.
- originais/: cópias byte a byte dos cinco insumos; a anotação original não foi corrigida silenciosamente.
- MANIFESTO_SHA256.txt: integridade desta entrega, independente do índice dos notebooks.

As fontes usadas são os textos PATSTAT preservados, resultados 08c, ficha humana recebida e critérios locais dos guias 08/08c. Não houve nova consulta ao PATSTAT ou ao artigo nem validação externa das alegações das patentes. A proveniência dos títulos/resumos continua desconhecida por aplicação.
