# Plano para o classificador

## Regra de entrada

O classificador só entra depois de a rede ser congelada. A avaliação contém os
SHA-256 dos cinco CSVs e do resumo da geração; `05_executar_modelo.py`
recusa um relatório de outra pasta ou arquivos modificados.

Como a topologia original não está disponível, o gate confirmatório permanece
bloqueado inclusive para a v13 de contagens exatas. A opção
`--permitir-rede-divergente` produz somente análise exploratória.

## Reconstrução

O perfil `reconstrucao_tcc_v1` conserva regressão logística, divisão 70/30,
100 repetições e limiares 0,50, 0,70 e 0,85. Demais parâmetros são hipóteses
explícitas. Word2vec e regressão agora têm todos os parâmetros operacionais no
JSON; o hash dos tokens é SHA-256 estável, sem depender de
`PYTHONHASHSEED`.

## Sensibilidade sem olhar o teste

- Desenvolvimento: 2006–2008.
- Confirmação fechada: 2009–2010.
- Métrica de seleção: average precision.
- ROC-AUC: reportado, nunca usado para imitar 0,91.
- Limite: 12–24 perfis pré-declarados.

O runner que materializa esses perfis ainda não foi implementado. Até existir,
o protocolo é uma especificação, não um resultado.

## Avaliação temporal

O executor `05_executar_modelo.py` mede predição contemporânea de ligações
ocultadas. O executor `11_avaliar_previsoes_temporais.py` avalia, separadamente,
pares ausentes no ano-base nos horizontes de 1, 3 e 5 anos.

O protocolo adotado considera a presença em qualquer ano entre o seguinte e o
fim do horizonte. Cada par recebe uma pontuação de um modelo ajustado em outros
grupos de candidatos do mesmo ano-base. A avaliação registra quantas rodadas
geram previsões, o volume previsto, a taxa agrupada e a média das rodadas com
previsões. As taxas ficam em branco quando não há previsões. O Top 20 é um
diagnóstico exploratório e as regras exatas usadas por Kochan seguem incertas.

Veja o [relatório final](RELATORIO_FINAL.md) e os [resultados](../runs/modelos/).
