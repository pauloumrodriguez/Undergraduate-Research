# Guia de execução completa — do zero aos resultados

Este roteiro reconstrói o que é reproduzível do estudo de Patrick Kochan sem
usar scripts, checkpoints ou redes da tentativa antiga.

## 1. Preparar o ambiente

Requisitos:

- Windows 10/11;
- Python 3.12;
- Java 21;
- Apache Solr 10.0.0.

No PowerShell, entre nesta pasta e crie um ambiente Python:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r .\requirements.txt
```

## 2. Conferir as entradas

Os arquivos `2006_USPTO.json` a `2015_USPTO.json` devem estar em
`dados/brutos/`. O vocabulário deve estar em
`dados/vocabulario/termos_carbono.txt`.

Gere os hashes e audite todos os registros:

```powershell
python .\src\01_gerar_manifestos.py --auditoria-completa
```

Saídas:

- `evidencias/manifesto_arquivos.csv`;
- `evidencias/resumo_manifesto.json`.

## 3. Criar uma coleção Solr isolada

Inicie o Solr a partir da instalação local:

```powershell
solr.cmd start
```

Crie uma coleção nova usando o configset fornecido nesta pasta:

```powershell
solr.cmd create -c patents_replicacao_nova -d .\solr\configset_replicacao
```

O configset contém os campos `id`, `Title`, `Abstract` e `Year`, além dos
mesmos arquivos de stopwords e sinônimos observados na auditoria.

Não reutilize a coleção antiga `patents` para esta execução.

## 4. Indexar as 2.000.147 patentes

```powershell
python .\src\00_indexar_solr_seguro.py
```

O indexador:

- lê diretamente os JSONs brutos;
- remove pontuação ASCII de título e resumo;
- envia documentos em lotes;
- confere as contagens anuais;
- não apaga automaticamente nenhuma coleção;
- grava `evidencias/indexacao.json`.

Se uma indexação válida for interrompida, confira a coleção e use:

```powershell
python .\src\00_indexar_solr_seguro.py --retomar
```

## 5. Validar e fotografar o Solr

```powershell
python .\src\02_validar_solr.py
```

Esse passo confere total, anos, schema, configuração e documentos-amostra. A
saída operacional é `evidencias/solr_snapshot_v2.json`.

## 6. Construir as variantes de rede

Uma execução deve sempre usar uma pasta nova. Exemplo para a interpretação
mais literal:

```powershell
python .\src\03_construir_redes.py `
  --variante v01_baseline_atual `
  --saida .\runs\reexecucao_do_zero\v01_baseline_atual
```

Para reconstruir todas as hipóteses declaradas:

```powershell
$variantes = @(
  'v01_baseline_atual',
  'v02_normalizacao_simetrica',
  'v03_consulta_analisada_and',
  'v04_148_posicoes',
  'v05_sem_alias_compartilhado',
  'v06_cumulativa',
  'v07_mesmo_campo_anual',
  'v08_mesmo_campo_cumulativa',
  'v09_apenas_resumo_cumulativa',
  'v10_apenas_titulo_cumulativa',
  'v11_apenas_termo_principal',
  'v12_termo_principal_mesmo_campo'
)

foreach ($variante in $variantes) {
  python .\src\03_construir_redes.py `
    --variante $variante `
    --saida ".\runs\reexecucao_do_zero\$variante"
}
```

Cada pasta recebe os CSVs anuais, o vocabulário auditado, o checkpoint e um
resumo da execução.

## 7. Avaliar uma rede

```powershell
python .\src\04_avaliar_redes.py `
  --redes .\runs\reexecucao_do_zero\v01_baseline_atual
```

Para interpretar redes anuais de forma cumulativa:

```powershell
python .\src\04_avaliar_redes.py `
  --redes .\runs\reexecucao_do_zero\v11_apenas_termo_principal `
  --cumulativa `
  --saida .\runs\reexecucao_do_zero\v11_apenas_termo_principal\avaliacao_cumulativa.json
```

## 8. Revalidar as provas e comparar as variantes

Depois de avaliar as pastas, execute:

```powershell
python .\src\07_revalidar_provas_tcc.py `
  --runs .\runs\reexecucao_do_zero `
  --aplicar
python .\src\06_comparar_variantes.py `
  --runs .\runs\reexecucao_do_zero `
  --saida .\evidencias\reexecucao_do_zero
```

O primeiro comando trata os valores 0/1 da Tabela 3 como ausência/presença de
ligação. O segundo gera `evidencias/comparacao_variantes.csv` e `.json`.

## 9. Reproduzir o diagnóstico pós-hoc v13

Depois de construir e avaliar a v11:

```powershell
python .\src\09_diagnostico_figura6.py `
  --redes-v11 .\runs\reexecucao_do_zero\v11_apenas_termo_principal `
  --saida .\evidencias\reexecucao_do_zero\diagnostico_pos_hoc_figura6.json `
  --exportar-v13 `
  --saida-v13 .\runs\reexecucao_do_zero\v13_ajuste_pos_hoc_exato
python .\src\04_avaliar_redes.py `
  --redes .\runs\reexecucao_do_zero\v13_ajuste_pos_hoc_exato
```

A v13 deve permanecer rotulada como pós-hoc. Ela é útil para demonstrar que
os totais publicados não determinam sozinhos a metodologia.

## 10. Executar o classificador exploratório

Exemplo usando a v11 e apenas uma repetição inicial:

```powershell
python .\src\05_executar_modelo.py `
  --redes .\runs\redes\v11_apenas_termo_principal `
  --avaliacao .\runs\redes\v11_apenas_termo_principal\avaliacao_redes.json `
  --perfil reconstrucao_tcc_v1 `
  --repeticoes 1 `
  --permitir-rede-divergente `
  --saida .\runs\modelos\exploratorio_v11_teste
```

Após validar o funcionamento, remova `--repeticoes 1` para usar as 100
repetições declaradas no perfil. Isso pode levar bastante tempo.

O rótulo exploratório é obrigatório porque as arestas originais não foram
publicadas. O script não permite transformar silenciosamente essa execução em
uma confirmação.

## 11. Validar a estrutura e rodar os testes

```powershell
python .\src\08_validar_pacote.py
```

Depois execute os testes do código:

```powershell
python -m unittest discover -s .\tests -p 'test_*.py' -v
```

## 12. Fechar o caderno de evidências

```powershell
python .\src\10_manifestar_evidencias.py
```

Esse comando gera os hashes de evidências, redes e recursos do Solr.

## O que seria necessário para uma réplica exata

Para confirmar igualdade com Patrick ainda seria necessário obter pelo menos
um destes itens:

- tabela `relation` original ou CSVs anuais das redes;
- lista dos 79 termos ativos;
- consultas Solr e código original;
- parâmetros completos do Node2Vec/Word2Vec e da amostragem.

Sem esses materiais, esta pasta oferece uma reconstrução auditável e completa
do que é possível reproduzir, mas não afirma identidade não demonstrada.
