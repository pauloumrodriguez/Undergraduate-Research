# Evidências

Esta pasta contém resultados de auditoria produzidos pela replicação nova.

- `comparacao_variantes.csv/json`: comparação consolidada das redes;
- `diagnostico_pos_hoc_figura6.json`: derivação e limites da v13;
- `avaliacao_baseline_atual.csv/json`: avaliação da interpretação inicial;
- `auditoria_assinaturas_historicas.json`: rastreabilidade dos runs entregues;
- `historico_auditoria/`: snapshot que sustentou a análise já concluída.

Ao reexecutar o pipeline do zero, também serão criados aqui:

- `manifesto_arquivos.csv` e `resumo_manifesto.json`;
- `indexacao.json`;
- `solr_snapshot_v2.json` para `patents_replicacao_nova`;
- `manifesto_evidencias.csv/json`.

O snapshot histórico não é usado automaticamente pelo novo construtor de
redes. Antes de uma reexecução, `02_validar_solr.py` deve produzir o snapshot
da coleção nova.
