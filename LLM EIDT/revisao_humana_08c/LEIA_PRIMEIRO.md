# Revisão humana das duas famílias do 08c

Preparado em 08/11/2026. Esta é uma etapa de desenvolvimento em CPU, sem nova inferência, treinamento ou alteração dos resultados congelados. As definições abaixo operacionalizam os guias locais 08/08c e os prompts v3; não constituem uma validação nova das definições do artigo.

## Como fazer

1. Abra ABRIR_REVISAO.html no Chrome ou Edge, dando dois cliques. Não requer Colab, GPU, instalação ou internet. Extraia o ZIP antes de abrir.
2. Identifique o anotador e registre se ele viu previsões ou comentários sobre elas. Paulo já recebeu exemplos nesta conversa: para esta revisão, escolha “Sim”. Outro anotador pode usar a mesma ficha em uma cópia separada e declarar sua própria exposição. Não envie a pasta de auditoria a quem produzirá uma referência independente.
3. Leia título e resumo de cada família. Preencha os seis grupos. O formulário começa vazio, sem sugestões do modelo. Clique em “Adicionar item” e use termos curtos com papel técnico claro. Copie literalmente a evidência do título e/ou resumo para os campos correspondentes. O programa confere a localização e registra posições em caracteres Unicode; ele não julga o significado.
4. Nos pares, informe dois IDs distintos de memes existentes, separados por vírgula. Nos efeitos, informe a categoria e, quando houver suporte, IDs de elementos relacionados. Os IDs aparecem em cada item. Não reutilize ID de par ou efeito nesses vínculos.
5. Se nenhum item for sustentado, escolha “Ausência de evidência após revisão”. Não use essa opção para campos não lidos. Dúvidas que não puder resolver devem ficar como “Indeterminado — requer adjudicação”, com explicação. Ambiguidades entre fontes devem ser preservadas, não completadas com conhecimento externo.
6. Baixe rascunhos durante o trabalho. O navegador NÃO salva automaticamente. Para continuar, abra novamente o HTML e importe o JSON baixado. Ao terminar clique em “Concluir e baixar revisão”. A conclusão confirma preenchimento e citações, não correção científica. Envie o JSON produzido ao pesquisador/assistente; preserve também uma cópia no Drive, em uma nova pasta revisao_humana_08c.

## Critérios por grupo

- **Memes técnicos:** técnicas, mecanismos, componentes ou princípios centrais e específicos no contexto. Não transformar palavras genéricas, numeração, redação jurídica ou etiquetas de fórmulas isoladas em tecnologia. Um componente pode ocupar outro papel, desde que cada anotação seja sustentada; isso não cria automaticamente uma convergência.
- **Funções:** o que a tecnologia explicitamente faz ou pretende fazer. Preservar modalidade, finalidade e negação. Uma alegação no resumo não equivale a eficácia comprovada experimentalmente.
- **Materiais:** substâncias, misturas ou suportes físicos/biológicos no papel de material. Condições clínicas, objetivos, propriedades e palavras da redação não são materiais apenas por aparecerem no texto.
- **Processos:** procedimentos ou operações técnicas descritos ou nomeados de modo explícito. Não inventar etapas ausentes nem transformar o ato de descrever a patente em processo técnico.
- **Pares de convergência:** dois memes distintos com integração técnica sustentada. Coocorrência, enumeração, relação genérica entre parte e todo ou duas designações do mesmo conceito não bastam. Registrar a integração em palavras e citar sua evidência. Não repetir par invertido. Na dúvida entre componente e integração, justificar e solicitar adjudicação; não presumir convergência.
- **Efeitos:** resultados explicitamente alegados e seu vínculo técnico quando disponível. Redução de custos exige menção explícita a economia/custo; ganho de eficiência exige um ganho explícito de eficiência ou relação entre recursos e desempenho. “Útil”, “otimizado” ou uma finalidade isolada não sustentam essas categorias automaticamente. Usar “outro” para resultados de outro tipo realmente expressos. Não inferir ganho, comparação, custo ou evidência experimental inexistentes.

## Unidade e evidência

Cada item representa um conceito no contexto; sinônimos não devem multiplicar achados. Registre o idioma do termo/descrição; não traduza as fontes. Use citações literais com contexto suficiente para incluir negações. Se a mesma citação aparecer mais de uma vez no mesmo campo, amplie-a para tornar a ocorrência única. Pode citar título e resumo no mesmo item. Evite copiar o resumo inteiro sem necessidade. O formulário não normaliza nem corrige os textos recebidos, inclusive caracteres incomuns.

As fontes de título e resumo podem ser aplicações diferentes da mesma família, e seus identificadores não foram registrados na extração antiga. Há possível divergência de finalidade entre título e resumo da família 50390156; registre interpretações por campo, sem fundir afirmações incompatíveis. Não é possível resolver a proveniência apenas com esta base. A ficha tem um campo para ambiguidades da família.

## O que esta etapa pode concluir

As famílias 68698300 e 50390156 são os extremos de comprimento das seis famílias de validação já usadas. Não são amostra representativa. Esta ficha é uma referência humana de desenvolvimento; não é automaticamente padrão-ouro, revisão cega, referência adjudicada ou teste independente. Se houver exposição às saídas, registrá-la. Uma só pessoa não permite medir concordância entre anotadores. Recomenda-se duas anotações separadas e adjudicação documentada; conservar originais e versão consolidada sem sobrescrever.

Depois da anotação, comparar candidatos e referência por conceito, papel e escopo, com correspondência um a um; pares sem ordem e efeitos com categoria e vínculos equivalentes. Registrar omissões, duplicatas, suporte insuficiente, categoria incorreta e indeterminação. Preservar a falha de geração como falha, não como ausência de achados. Não calcular precisão/F1 sobre rascunhos ou casos indeterminados silenciosamente. Esta entrega não calcula métricas semânticas, não altera prompts e não escolhe modelo.

Somente após revisão/adjudicação e análise dos erros decidir se há uma correção de protocolo demonstrável. Novas regras precisam de versão e nova avaliação em validação, sem ajustar aos resultados das 20 famílias de teste. Antes de expandir às 200 famílias, congelar protocolo e critérios de aceitação e avaliar extração com referência humana; o teste CPC anterior não valida extração. O alinhamento E5 permanece posterior a essa decisão.

## Arquivos e rastreabilidade

- ABRIR_REVISAO.html: formulário com as fontes incorporadas; funciona mesmo sem outros arquivos ao lado.
- textos_originais.json: cópia exata dos títulos/resumos utilizados, com hash registrado no formulário.
- auditoria_automatica_abrir_depois/: resultados brutos recebidos e diagnóstico assistido, fora da ficha de anotação. Não é anotação humana nem resposta correta pré-preenchida.
- MANIFESTO_SHA256.txt: hashes deste pacote. Não substitui SHA256SUMS.txt do projeto.

O JSON exportado tem esquema próprio revisao-humana-08c-1.0. Não substitui entradas do treinamento, extracoes.jsonl ou o schema canônico do modelo. Grupos pendentes/indeterminados permanecem explicitamente marcados. O pacote é aditivo e independente do ambiente Colab; notebooks anteriores não precisam ser executados.
