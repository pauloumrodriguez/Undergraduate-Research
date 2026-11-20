# Validação local da entrega brasileira

Verificação em 3 de novembro de 2026, com Python 3.12 local. O validador `jsonschema==4.25.1` foi instalado em uma pasta isolada de testes. Nenhum modelo de linguagem foi carregado.

## Dados reais

- Conferido SHA-256 do ZIP de origem contra o valor fixado na configuração.
- Validadas 1.000 famílias DOCDB distintas, completude dos textos/CPC e correspondência com as partições originais 800/100/100.
- Filtro ANY CPC A61/C12N: 960 elegíveis e 40 excluídas.
- Amostra resultante: 200 famílias únicas; janelas 67/67/66; partições 160/20/20, preservadas em relação à origem.
- Título/resumo: 185 pt/pt, 5 en/en, 9 pt/en e 1 en/pt.
- SHA-256 do CSV selecionado: `9cf3747f8dec5cc9add77ce2632a63abe678dcf860feb56b6215cdf09c91cf74`.
- Pré-processamento real gerou 200 entradas de extração, 200 registros de metadados e arquivos CPC com 160/20/20 linhas. Os hashes estão na auditoria de pré-processamento.

## Integridade e comportamento

O teste do seletor confirmou seleção determinística, preservação dos textos e rótulos, isolamento das famílias e recusa de entrada com hash divergente, família duplicada, rótulo adulterado ou configuração incompatível. Saídas diferentes já existentes são recusadas.

Oito testes do pré-processamento/validador passaram. Eles cobrem registros com idiomas mistos, exclusão de CPC do prompt, preservação dos originais e das partições, normalização Unicode, reexecução idempotente e rejeição de evidência inventada, idioma incoerente, referência inexistente, par de convergência duplicado e resposta incompleta. O caso de preparação também verifica a rejeição de CSV alterado após a seleção.

As células Python dos notebooks ativos foram compiladas para verificar sintaxe. Células têm IDs únicos, contadores de execução vazios e nenhuma saída salva. Os notebooks 00, 02 e 03 foram exercitados localmente com pasta de Drive simulada. Reexecuções confirmaram idempotência e preservação de um manifesto editável existente.

## Limites da validação

A montagem/autorização do Google Drive foi substituída por uma pasta temporária durante os testes locais. A execução real no Colab, a instalação no ambiente Colab e o diagnóstico de GPU atualizado não foram realizados nesta entrega. Os relatórios antigos de GPU informados pelo pesquisador não foram reescritos.

Treinamento, extração Qwen3-8B, embeddings, alinhamento e indicadores ainda não foram executados. Verificação estrutural e citações literais não equivalem a avaliação humana da interpretação técnica. A cobertura de rótulos CPC e as limitações de proveniência estão registradas na auditoria metodológica.
