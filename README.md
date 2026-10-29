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
- evidências, hashes e comparações, em `evidencias/`;
- testes automatizados, em `tests/`;
- documentação e o veredicto científico, em `docs/`.

## Resultado científico em uma frase

Foi possível reconstruir o corpus, testar hipóteses de coocorrência e aproximar
muito as contagens publicadas. Também foi possível reproduzir os totais por um
ajuste pós-hoc. Entretanto, não foi possível confirmar que as arestas, pesos e
parâmetros são os mesmos do autor, porque esses elementos não foram publicados.

Por isso, a predição de ligações permanece **exploratória**, e não uma
reprodução confirmatória do classificador original.

## Por onde começar

1. Leia `docs/ESTRUTURA_DA_PASTA.md`.
2. Leia `docs/GUIA_EXECUCAO_COMPLETA.md`.
3. Abra `notebooks/00_leia_primeiro.ipynb`.
4. Consulte `docs/RELATORIO_AUDITORIA_RECEITA.md` para o veredicto.

## Fluxo completo

```text
dados brutos
  -> auditoria e manifesto
  -> indexação segura no Solr
  -> validação do índice
  -> construção das variantes de rede
  -> avaliação e comparação
  -> classificador exploratório
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
