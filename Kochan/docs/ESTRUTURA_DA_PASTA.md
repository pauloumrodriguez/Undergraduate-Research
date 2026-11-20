# Estrutura da pasta

| Pasta | Conteúdo | Função |
|---|---|---|
| `dados/` | JSONs brutos e vocabulário | Entradas imutáveis |
| `referencias/` | TCC e artigo | Fontes publicadas |
| `config/` | Alvos, variantes e modelos | Regras declaradas |
| `src/` | Scripts Python | Execução do pipeline |
| `notebooks/` | Roteiros didáticos | Exploração e compreensão |
| `runs/redes/` | CSVs e avaliações por variante | Resultados das redes |
| `runs/modelos/` | Saídas futuras do classificador | Resultados exploratórios |
| `evidencias/` | Snapshots, comparações e hashes | Rastreabilidade |
| `tests/` | Testes automatizados | Controle de qualidade |
| `solr/` | Stopwords, sinônimos e instruções | Configuração da busca |
| `docs/` | Relatórios e decisões | Interpretação científica |

## Tipos de arquivo

- `.py`: programa executável;
- `.ipynb`: notebook didático;
- `.csv`: tabela que pode ser aberta no Excel;
- `.json`: configuração ou resultado estruturado;
- `.md`: documento de leitura;
- `.pdf`: fonte original.

## Regra mental

`config` diz o que fazer; `src` executa; `runs` guarda o resultado;
`evidencias` prova como ele foi obtido; `docs` explica o significado.

O script `src/08_validar_pacote.py` confere automaticamente se essa estrutura,
os JSONs e os notebooks estão íntegros.
