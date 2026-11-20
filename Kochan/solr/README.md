# Solr

O projeto original não preserva versão, schema, analisadores e configset
suficientes para reconstrução exata. Esta pasta documenta a coleção local sem
apresentá-la como configuração de Patrick.

## Configuração fornecida

- `configset_replicacao/`: configset completo para a coleção nova;
- `configset_export/stopwords.txt`;
- `configset_export/synonyms.txt`.

O snapshot que sustentou a auditoria já concluída está em
`evidencias/historico_auditoria/solr_snapshot_colecao_patents.json`. Uma
reexecução do zero deve gerar um novo `evidencias/solr_snapshot_v2.json` para
a coleção `patents_replicacao_nova`.

O fingerprint é da evidência capturada; não é um hash byte a byte de todo o
índice. Antes de construir uma rede, o programa compara o Solr vivo com
contagens, amostras, schema/config e recursos do snapshot v2.

## Procedimento recomendado

1. criar `patents_replicacao_nova` com `configset_replicacao/`;
2. conferir `id`, `Title`, `Abstract` e `Year`;
3. registrar Solr, Lucene e Java;
4. preservar os recursos do analisador;
5. indexar com `00_indexar_solr_seguro.py`;
6. executar `02_validar_solr.py`;
7. usar uma pasta nova para cada variante;
8. nunca reutilizar checkpoint de outra assinatura.

Analisadores diferentes são variantes metodológicas e nunca devem compartilhar
a mesma pasta de resultados.
