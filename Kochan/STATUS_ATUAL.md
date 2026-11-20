# Estado da replicação nova

Atualizado em 28/10/2026.

## Organização

- Esta pasta é independente da primeira tentativa de replicação.
- Não contém código, checkpoints, CSVs corrigidos ou modelos legados.
- Os dados brutos foram mantidos como entradas imutáveis.
- O pipeline novo processa os textos diretamente durante a indexação.

## Verificado

- 2.000.147 patentes e 2.000.147 identificadores únicos;
- contagens anuais do corpus;
- schema e conteúdo relevante do Solr auditados;
- 148 posições e 147 conceitos únicos no apêndice;
- 50 nós legíveis na Figura 6;
- seis provas binárias da Tabela 3;
- variantes metodológicas de consulta e rede;
- testes automatizados do pipeline.

## Melhor aproximação

`v11_apenas_termo_principal`, interpretada cumulativamente, contém todos os 50
nós publicados de 2006 e mais seis. Ela aproxima bem os totais, mas contraria
partes da descrição textual porque ignora sinônimos.

## Encaixe exato

`v13_ajuste_pos_hoc_exato` reproduz 50/261, 52/325, 54/359, 59/397 e 63/461.
Como oito exclusões foram inferidas dos próprios alvos, a variante é uma
análise de sensibilidade pós-hoc, não uma confirmação independente.

## O que continua não verificável

- lista original dos 79 termos ativos;
- tabela original de relações, arestas e pesos;
- consultas Solr exatas;
- configuração completa de Node2Vec/Word2Vec;
- estratégia exata de amostragem negativa;
- executor temporal de horizontes 1/3/5 anos.

Assim, o classificador só pode ser tratado como exploração até que o autor
forneça pelo menos a rede original, o código ou as consultas.
