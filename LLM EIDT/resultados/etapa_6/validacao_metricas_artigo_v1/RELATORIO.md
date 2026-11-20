# Validação das métricas contra as Tabelas 6–9 do artigo

19/11/2026. Gerado por `scripts/validar_metricas_artigo.py` (dados em `dados/referencia/tabelas_6_8_artigo_transcritas.json`). Detalhes e ressalvas em `docs/EDH_METRICAS_V1.md`; números em `validacao.json`.

| Janela | P/R/F1 (regra escrita) | NDCG adotado × publicado |
|---|---|---|
| 2010–14 | confere (0,7500 / 0,8571 / 0,8000) | 0,9872 × 0,9961 |
| 2015–19 | não confere (0,6250 / 0,8333 / 0,7143); confere só com o corte gráfico inferido (1,0000 / 0,8000 / 0,8889) | indeterminado: tabela com temas repetidos e ausentes (0,9485 a 0,9507 nas hipóteses × 0,7597) |
| 2020–24 | confere (1,0000 / 0,9091 / 0,9524) | 0,9762 × 0,7366 |

A média publicada da Tabela 9 é consistente com as três linhas. O NDCG publicado não é reproduzível pela convenção adotada nem por variantes testadas exploratoriamente (não adotadas). Validação da implementação, não do método.
