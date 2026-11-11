# Estado da replicação nova

Atualizado em 11/11/2026.

## Organização

- Esta pasta é independente da primeira tentativa de replicação.
- Não contém código, checkpoints, CSVs corrigidos ou modelos legados.
- Os dados brutos foram auditados como entradas imutáveis e permanecem fora do
  GitHub devido ao tamanho; seus hashes são preservados no manifesto.
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

## Experimento final com a v11 anual

- Dez redes anuais de 2006 a 2015.
- 100 repetições por ano-base de 2006 a 2010 no teste de ligações ocultadas. ROC-AUC média de 0,7152.
- Outras 100 repetições por ano-base na avaliação em até 1, 3 e 5 anos.
- Top 20 em até cinco anos: 32,3% de acerto em média, frente a 21,3% entre todos os candidatos.
- Zero previsões nos limiares publicados. Os 53,98% de Kochan ficaram sem reprodução.

Veja o [relatório final](docs/RELATORIO_FINAL.md) e os [resultados completos](runs/modelos/).

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
- regras exatas do protocolo temporal original.

Assim, o classificador só pode ser tratado como exploração até que o autor
forneça pelo menos a rede original, o código ou as consultas.
