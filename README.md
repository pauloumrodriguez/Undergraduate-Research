# Replicação nova e independente de Kochan

Esta pasta contém apenas a reconstrução melhorada preparada a partir do TCC
de 2022 e do artigo de 2024 de Patrick Kochan. Ela não contém os scripts,
checkpoints, redes corrigidas ou modelos da primeira tentativa de replicação.

## O que está incluído

- a estrutura, os hashes e as instruções para os dez arquivos brutos do
  corpus USPTO-2M, que devem ser colocados em `dados/brutos/`;
- o vocabulário usado na reconstrução, em `dados/vocabulario/`;
- os PDFs de referência, em `referencias/`;
- configurações metodológicas explícitas, em `config/`;
- scripts Python numerados, em `src/`;
- notebooks didáticos, em `notebooks/`;
- resultados CSV/JSON das variantes de rede, em `runs/redes/`;
- avaliações do classificador e das previsões em 1, 3 e 5 anos, em `runs/modelos/`;
- evidências, hashes e comparações, em `evidencias/`;
- testes automatizados, em `tests/`;
- documentação e o veredicto científico, em `docs/`.

## Resultados finais

A v11 anual cobre 2006 a 2015 e tem 90 termos ativos, 759 pares distintos
e 3.340 registros de par por ano. No teste de ligações ocultadas, a ROC-AUC
média de 2006 a 2010 foi **0,7152**, frente a **0,91** no estudo.

Na avaliação temporal, o Top 20 teve **32,3%** de acerto em até cinco anos,
frente a **21,3%** entre todos os candidatos. Nenhum par atingiu os limiares
publicados de 50%, 70% ou 85%. A avaliação é exploratória, com rede e
protocolo reconstruídos a partir das informações disponíveis.

## Por onde começar

1. Leia o [relatório final](docs/RELATORIO_FINAL.md).
2. Abra o [roteiro de apresentação](docs/roteiro_apresentacao_kochan.pdf).
3. Consulte os [resultados dos modelos](runs/modelos/) e as [redes anuais da v11](runs/redes/v11_anual_2006_2015/).
4. Siga o [guia de execução](docs/GUIA_EXECUCAO_COMPLETA.md). Os testes dos modelos podem ser refeitos com os CSVs publicados, sem o Solr ou os JSONs brutos.

## Fluxo completo

```text
dados brutos
  -> auditoria e manifesto
  -> indexação segura no Solr
  -> validação do índice
  -> construção das variantes de rede
  -> avaliação e comparação
  -> classificador exploratório
  -> avaliação temporal em 1, 3 e 5 anos
  -> manifesto final das evidências
```

Os comandos completos estão em `docs/GUIA_EXECUCAO_COMPLETA.md`.

## Dados grandes não versionados

Os dez JSONs brutos somam aproximadamente 1,65 GiB e vários excedem o limite
normal de 100 MiB por arquivo do GitHub. Por isso eles não são enviados ao
repositório. O manifesto preserva seus nomes, tamanhos e SHA-256. Para uma
reexecução integral, coloque `2006_USPTO.json` a `2015_USPTO.json` em
`dados/brutos/` e execute a auditoria descrita no guia.

## Três redes que não devem ser confundidas

- `v01_baseline_atual`: interpretação mais literal do TCC, mas divergente.
- `v11_apenas_termo_principal`: melhor candidata empírica não pós-hoc.
- `v13_ajuste_pos_hoc_exato`: reproduz os totais, mas foi ajustada a partir
  dos próprios alvos e não confirma o método original.

## Regra de segurança científica

O script `05_executar_modelo.py` bloqueia modelagem confirmatória enquanto a
topologia original não puder ser comprovada. A execução exploratória exige a
opção explícita `--permitir-rede-divergente`.
