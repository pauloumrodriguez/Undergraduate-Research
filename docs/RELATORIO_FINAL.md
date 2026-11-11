# Relatório final da replicação exploratória de Kochan

Referências de comparação: TCC de Patrick Kochan (2022), seções 5.2 e 5.3, e artigo de 2024, seções 5.1 e 5.2.

## 1. Corpus e rede de coocorrências

Validamos 2.000.147 patentes USPTO-2M, com contagens anuais conferidas de 2006 a 2015. A variante v11 anual usa o termo principal de cada entrada do vocabulário de carbono, sem expandir os sinônimos. A rede de 2006 passou nos seis testes de presença e ausência de ligação da Tabela 3 do TCC.

Nos dez CSVs anuais, contamos **90 termos ativos, 759 pares distintos e 3.340 registros de par por ano**. Kochan reportou 79 termos e 3.719 coocorrências. O total de termos diverge. A comparação entre 3.340 e 3.719 depende de confirmar a unidade de contagem de Kochan.

## 2. Classificador no teste de ligações ocultadas

Mantivemos a divisão 70/30 e fizemos 100 repetições com a v11 anual para cada ano-base. A tabela resume a capacidade de distinguir ligações ocultadas e pares sem ligação no próprio ano.

| Ano-base | Nossa ROC-AUC média | Desvio-padrão das repetições | ROC-AUC de Kochan |
|---|---:|---:|---:|
| 2006 | 0,7260 | 0,0630 | 0,89 |
| 2007 | 0,6940 | 0,0678 | 0,91 |
| 2008 | 0,7081 | 0,0717 | 0,91 |
| 2009 | 0,7211 | 0,0635 | 0,93 |
| 2010 | 0,7267 | 0,0556 | 0,91 |

A média das cinco médias anuais foi **0,7152**, abaixo de **0,91** publicado. O desvio-padrão descreve a variação com a semente na mesma rede de cada ano.

## 3. Avaliação temporal

Fizemos outras 100 repetições por ano-base. O treinamento usa somente o ano-base, e cada candidato é pontuado fora do grupo usado no ajuste correspondente. O par candidato precisa estar ausente na rede do ano-base e ter ambos os termos ativos. Contamos acerto se ele aparece em pelo menos um ano entre o ano seguinte e o fim do horizonte. Com redes anuais, essa regra também admite pares que reaparecem depois de já terem ocorrido antes do ano-base.

| Horizonte | Taxa média no Top 20 | Taxa média entre todos os candidatos |
|---|---:|---:|
| Até 1 ano | 10,9% | 6,5% |
| Até 3 anos | 24,9% | 15,2% |
| Até 5 anos | 32,3% | 21,3% |

Cada taxa da tabela é a média simples dos cinco anos-base. O Top 20 exploratório ficou acima da taxa de referência média em todas as 15 combinações de ano-base e horizonte, com variação entre repetições.

Nas 500 rodadas temporais, nenhum par atingiu os limiares publicados de 50%, 70% ou 85%. A taxa de acerto ficou indefinida nesses limiares. Os **53,98%** de Kochan a cinco anos e limiar de 85% ficaram sem reprodução.

## 4. Conclusão e evidências

A reconstrução exploratória está concluída. A v11 mostrou capacidade de priorizar pares que apareceram depois, em média, e apresentou ROC-AUC inferior à publicada. A confirmação da replicação exata depende das consultas ou das relações originais e dos detalhes de treinamento e avaliação de Kochan.

- [Relações anuais da v11](../runs/redes/v11_anual_2006_2015/)
- [Resumo do teste de ROC-AUC](../runs/modelos/roc_auc_v11_100_repeticoes/resumo.csv)
- [Ranking Top 20 consolidado](../runs/modelos/temporal_v11_100_repeticoes/ranking_top20_consolidado.csv)
- [Limiar e horizonte consolidados](../runs/modelos/temporal_v11_100_repeticoes/limiares_consolidados.csv)
- [Roteiro de apresentação](roteiro_apresentacao_kochan.pdf)
