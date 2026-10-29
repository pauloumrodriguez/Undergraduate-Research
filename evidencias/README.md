# Evidências

Esta pasta contém resultados de auditoria produzidos pela replicação nova.

- `comparacao_variantes.csv/json`: comparação consolidada das redes;
- `diagnostico_pos_hoc_figura6.json`: derivação e limites da v13;
- `avaliacao_baseline_atual.csv/json`: avaliação da interpretação inicial;
- `auditoria_assinaturas_historicas.json`: rastreabilidade dos runs entregues;

O snapshot integral que sustentou a análise local não é publicado porque
contém caminhos específicos da máquina. O schema, o configset portátil, os
recursos textuais e os resultados derivados necessários à reprodução estão
preservados nas demais pastas.

Ao reexecutar o pipeline do zero, também serão criados aqui:

- `manifesto_arquivos.csv` e `resumo_manifesto.json`;
- `indexacao.json`;
- `solr_snapshot_v2.json` para `patents_replicacao_nova`;
- `manifesto_evidencias.csv/json`.

Antes de uma reexecução, `02_validar_solr.py` deve produzir o snapshot da
coleção nova.
