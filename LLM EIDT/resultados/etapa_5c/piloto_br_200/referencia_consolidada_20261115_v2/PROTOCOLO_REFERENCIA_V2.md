# Regras consolidadas da referência 08c — versão 2

Registro em 15/11/2026. Decisões humanas D1–D5 recebidas no chat; implementação pelo assistente. Não altera retroativamente os prompts do 08c nem o resultado das gerações.

1. Memes: unidade técnica contextualizada e central. Propriedades físico-químicas são atributos; métodos usados apenas para caracterização/controle não são memes centrais. Rótulos genéricos isolados de fórmula são excluídos.
2. Processos: operações explicitamente nomeadas são elegíveis, sem exigir etapas detalhadas. Seleção, conversão, determinação da absorção e medição da rugosidade são itens separados.
3. Unidade: manter modalidades/alternativas conjuntas (prevenção ou tratamento; atenuar ou prevenir adesão e/ou vascularização). Separar entidades materiais distintas. Correspondências um a um, sem unir respostas do modelo após geração nem atribuir crédito múltiplo.
4. Função versus efeito: finalidade fica em funções, sem duplicação automática em efeitos. Ausência de efeitos na 50390156; alegação terapêutica da 68698300 mantida em categoria outro, como alegação sem comprovação apresentada. Custo/eficiência exigem suporte explícito.
5. Proveniência: origem documental de título/resumo não identificada; manter finalidades diferentes sem afirmar documentos distintos. Citação humana da função do resumo usa e/ou.

## Regras operacionais da comparação assistida

Uma abreviação pode ser desambiguada pelo contexto da evidência, preservando conceito/papel. Operadores e alternativas não podem ser alterados: “tratamento” sozinho não equivale a “prevenção ou tratamento”, e “e” não equivale a “e/ou”. Menção em outro grupo não recupera item na avaliação por campo. Efeitos também precisam de categoria e vínculos sustentados. Essas aplicações são escolhas operacionais do assistente documentadas, não novas decisões atribuídas ao usuário.

As métricas são condicionais à lista de referência atual e ao mapeamento assistido. Memes “substrato sólido” e “processo para seleção” na família longa não foram individualmente adjudicados; sua falta de correspondência não prova erro. Revisar cobertura não autoriza inserir itens silenciosamente. Não anunciar F1 definitivo, independência ou ganho estatístico de LoRA. A referência consolidada decorre da exposição às previsões e das decisões de um anotador.

## Sequência recomendada para desenvolvimento

A etapa documental D1–D5 está concluída. Antes de uma nova execução, preparar uma versão separada do protocolo de geração que incorpore essas regras e registre orçamento e critérios de aceitação. Preservar 08c e seus resultados. Usar somente validação; não ajustar com as 20 famílias de teste. É possível avaliar engenharia nas mesmas duas famílias, mas melhora nelas é ajuste de desenvolvimento, não generalização. Validar depois em outras famílias com referência preparada antes da inspeção das previsões. Não iniciar treinamento novo, alinhamento ou aplicação às 200 famílias apenas com estes resultados.

Nenhum notebook novo nem inferência foram executados nesta entrega. Não repetir 08c: ele ainda usa as instruções anteriores. A mudança de geração será uma entrega separada (08d), a ser implementada e testada antes de uso no Colab.
