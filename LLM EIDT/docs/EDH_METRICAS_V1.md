# EDh e métricas de identificação — versão 1

19/11/2026. Implementação em CPU, só biblioteca padrão. Não usa dados de patentes do piloto: as etapas anteriores (alinhamento, novidade, DP/CP, temas) ainda não existem. Não calcula nem fabrica Dh.

## O que foi implementado

`scripts/edh_metricas.py`

| Função | O que faz | Origem |
|---|---|---|
| `rotulo_dp` | DP se convergência E (função OU padrão); senão CP | Eq. 14 |
| `h_index` | maior h com ao menos h valores ≥ h | Eq. 15 |
| `edh_por_tema` | EDh por tema: só patentes DP; relações distintas e sem ordem; tema sem DP = 0 | Eq. 15 + `adotado.indices.edh` |
| `temas_a_partir_da_media` | corte pela média aritmética exata (Fraction), com igualdade por padrão | `adotado.indices.corte_principal` |
| `precisao_revocacao_f1` | P/R/F1 entre dois conjuntos; indefinido vira `None`, nunca 0 ou 1 | Seção 4.4 |
| `ndcg` | ordem por EDh decrescente, ganho linear = Dh, 1/log2(posição+1), empate pela média do bloco, IDCG por Dh decrescente | `adotado.indices.ndcg_reconstruido` |

`tests/test_edh_metricas.py`: 23 testes (h-index, EDh sem DP, relações invertidas e repetidas, invariante da ablação sem `C_conv`, média com igualdade e limiar fracionário, P/R/F1 indefinidos, NDCG calculado à mão, empates, IDCG zero). Rodar: `python -I -m unittest discover -s tests` na raiz do projeto.

## Validação contra o artigo

`scripts/validar_metricas_artigo.py` recalcula a Tabela 9 a partir das Tabelas 6–8, transcritas em `dados/referencia/tabelas_6_8_artigo_transcritas.json`. Resultado em `resultados/etapa_6/validacao_metricas_artigo_v1/`.

| Janela | P/R/F1 pela regra escrita (≥ média) | NDCG (convenção adotada) |
|---|---|---|
| 2010–14 (Tab. 6) | **confere**: 0,7500 / 0,8571 / 0,8000 | 0,9872 contra 0,9961 publicado |
| 2015–19 (Tab. 7) | **não confere**: 0,6250 / 0,8333 / 0,7143 contra 1,0000 / 0,8000 / 0,8889 | não calculável sem decidir a identidade dos temas |
| 2020–24 (Tab. 8) | **confere**: 1,0000 / 0,9091 / 0,9524 | 0,9762 contra 0,7366 publicado |

- **P/R/F1 reproduzem a Tabela 9 em 2 de 3 janelas pela regra escrita.** Na Tabela 7, só o "corte gráfico" (8 primeiros de EDh contra 10 primeiros de Dh) reproduz 1,0000 / 0,8000 / 0,8889. Essa leitura é inferida dos números da Tabela 9 e de `experimento.json`, não do texto do artigo.
- **A média da Tabela 9 é aritmeticamente consistente** com as três linhas publicadas (0,9167 / 0,8554 / 0,8804 / 0,8308).
- **Tabela 7:** a coluna Dh repete Biotechnology e Cell culture & engineering e omite Gene therapy e Biomaterials & delivery. Duas hipóteses de identidade para as duas últimas linhas dão NDCG de 0,9507 e 0,9503; usando só os 14 temas com Dh, 0,9485. Nenhuma se aproxima de 0,7597.
- **O NDCG publicado não é reproduzível** pela convenção adotada, nem por nenhuma das variantes tentadas: em 2020–24 a convenção adotada dá 0,9762 contra 0,7366 publicado, uma diferença que nenhuma escolha plausível de desempate explica.

## Divulgação sobre a busca de convenções

Antes de escrever o código, testei uma grade de convenções alternativas (ganho linear, exponencial 2^rel−1, ao quadrado, por posição, binário; desempate pela média, pela ordem impressa, melhor e pior caso; descontos 1/log2(p+1), 1/log2(p), 1/p, sem desconto; cortes @3 a @16) para ver se alguma reproduzia os dois NDCG publicados. **Nenhuma reproduziu os dois ao mesmo tempo.** Algumas aproximam um valor isoladamente (por exemplo, ganho exponencial com ordem impressa dá 0,9961 em 2010–14, mas 0,8538 em 2020–24). Isso foi exploratório e **não é adotado**: a convenção do projeto continua a registrada em `config/experimento.json` antes desta verificação. Adotar outra por ela casar com um valor seria ajuste ao alvo. O relatório de validação lista só quatro dessas variantes, como sensibilidade.

## O que isto não faz

- Não roda sobre dados do piloto: as entradas (relações novas, rótulos DP, temas) dependem de etapas não implementadas.
- Não define o Dh. O NDCG recebe um Dh dado como relevância.
- Não resolve a divergência da Tabela 11 (a ablação sem `C_conv` deve manter o EDh; o artigo mostra queda). O teste documenta o invariante.
- Os resultados deste módulo sobre as tabelas do artigo validam a **implementação**, não o método.

## Decisão pendente

Para a replicação, o NDCG do artigo precisa ser tratado como não reproduzível. Pedir aos autores a implementação do NDCG e as tabelas completas (com Dh por tema na Tabela 7) é o caminho para fechar isso.
