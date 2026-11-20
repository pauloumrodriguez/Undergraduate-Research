# Dados de entrada

## `brutos/`

Contém `2006_USPTO.json` a `2015_USPTO.json`. Esses são os únicos arquivos de
patentes necessários para iniciar o pipeline. Eles são tratados como entradas
imutáveis e não devem ser editados.

Os antigos arquivos `*_processado.json` não são necessários: o novo indexador
remove a pontuação de título e resumo durante a carga para o Solr.

## `vocabulario/`

`termos_carbono.txt` contém os conceitos e aliases usados nas consultas. O
pipeline registra seu SHA-256 em cada execução para impedir trocas silenciosas.
