# Proveniência e limitações

## Fontes científicas

- TCC de Patrick Davila Kochan, 2022: *Um Método de Análise de Patentes
  Voltado à Previsão de Tecnologias*.
- Artigo de 2024: *Identifying Technological Trends: A Patent Analysis Method
  for Technology Forecasting*.

As cópias usadas estão em `referencias/` e entram no manifesto do projeto.

## Corpus

O corpus local contém exatamente 2.000.147 registros nos anos publicados. A
auditoria completa confirmou IDs únicos e as contagens anuais. Ainda faltam a
URL/data formal de obtenção e a explicação documental do corte de 2015.

## Solr

`evidencias/historico_auditoria/solr_snapshot_colecao_patents.json` preserva a
captura que sustentou a auditoria entregue. Uma execução integral desta pasta
gera um novo `evidencias/solr_snapshot_v2.json` para a coleção isolada
`patents_replicacao_nova`. O snapshot registra schema/config efetivos, nove
documentos-amostra e os recursos `stopwords.txt` e `synonyms.txt`.

`solr/configset_replicacao/` contém o configset completo usado para criar a
coleção nova. `solr/configset_export/` preserva separadamente os dois recursos
textuais comparados na auditoria.

O fingerprint v2 identifica essa evidência, não cada byte dos 2.000.147
documentos. O construtor confere contagens, amostras, schema/config e recursos
contra o Solr vivo antes de usar um checkpoint.

## Linhagem dos runs

O código mudou durante a rodada inicial de hipóteses. v01–v05 são consistentes
internamente, mas o gerador exato não foi preservado. v07 e v09–v12 tiveram as
assinaturas confirmadas contra o gerador pré-finalização. O registro completo
está em `evidencias/auditoria_assinaturas_historicas.json`.

O gerador final inclui seu próprio hash e o fingerprint do snapshot na assinatura.
Resultados novos nunca devem sobrescrever as pastas históricas.

## Resultados

Os alvos publicados ficam em `config/alvos_publicados.json`. Contagens, pares
da Tabela 3 e rótulos da Figura 6 são testes externos. A v13 usa esses alvos
para derivar exclusões e, por isso, é marcada como pós-hoc e não confirmatória.

As arestas e pesos originais não foram publicados. Nem mesmo uma coincidência
perfeita de contagens e rótulos prova identidade topológica.
