# Adaptação metodológica brasileira — PATSTAT

Registro de decisão em 3 de novembro de 2026. Protocolo `llm-eidt-br-patstat-piloto-200-8b`, versão 3.0. Piloto `br_patstat_200_qwen3_8b_v1`.

## Definição do estudo

Este projeto adapta o método LLM-EIDT ao contexto brasileiro. A fonte empírica é uma extração anterior do PATSTAT Global, da European Patent Office (EPO), realizada no ambiente PROD da EPO Technology Intelligence Platform. O pacote de 1.000 famílias DOCDB foi fornecido pelo pesquisador e seu reaproveitamento foi autorizado. A definição atual substitui a coleta nova no AI Pat+ prevista no protocolo anterior.

O vínculo com o Brasil corresponde a pedido depositado no escritório brasileiro ou participação de inventor/depositante com país BR na consulta original. Isso não implica que todos os membros da família, todos os textos ou o pedido representante sejam brasileiros. A expressão “patentes brasileiras” deve ser apresentada como “famílias de patentes com vínculo com o Brasil”.

O período adotado é 2010–2024, inclusive. O escopo tecnológico solicitado é A61 ou C12N. O corpus chinês, o Qwen3-14B e os resultados do artigo permanecem documentados no bloco `publicado` de `experimento.json`. A execução brasileira usa Qwen3-8B e o encoder `intfloat/multilingual-e5-large`, com revisões fixadas. Seu objetivo imediato é validar o funcionamento do pipeline; não se pressupõe equivalência de desempenho ou reprodução dos valores do artigo.

## Proveniência e recorte verificável

Foram inspecionados o notebook de extração original, o ZIP, seu manifesto, o CSV completo e as partições JSONL. O arquivo com sufixo `preview.csv` contém as 1.000 famílias. O ZIP é preservado sem alteração em `dados/brutos/patstat_br_1000/LLM_EIDT_LORA_1000.zip`.

SHA-256 do ZIP: `09cf45526d9270cd92ed1d7d4339166f4562e92576c47a24353c753f4e6a5283`.

Há uma diferença relevante entre a consulta antiga e o escopo atual. A consulta antiga aceitava **IPC A61, C12N ou C12Q**. O pacote exportou CPCs de membros da família, mas não conservou os IPCs usados no filtro. Por isso, este piloto aplica, antes do sorteio, o critério verificável **existência de pelo menos um CPC com prefixo A61 ou C12N**. São examinados todos os códigos da família. C12Q sozinho não basta; famílias que também tenham C12Q continuam elegíveis quando satisfazem A61/C12N.

Esse recorte mantém **960 famílias e exclui 40**. Ele operacionaliza o escopo IPC/CPC solicitado por meio dos CPCs disponíveis. Não é uma reconstrução de um filtro IPC A61/C12N sobre toda a base PATSTAT. Famílias com IPC elegível e sem CPC correspondente podem ficar de fora. Os IDs excluídos e a regra aplicada constam em `dados/processados/piloto_br_200/auditoria.json`.

Não houve nova consulta ao PATSTAT nesta entrega. O vínculo BR está documentado no código original, mas as relações entre pessoas e pedidos não foram exportadas, impedindo sua revalidação individual somente com o pacote. A edição do PATSTAT e a data original de extração permanecem desconhecidas. A data deste registro não substitui a data de extração.

## Unidade, estratos e partições

A unidade é a **família DOCDB**, identificada por `patent_id` na fonte e `id_familia_docdb` no piloto. Um registro é mantido por família. A janela temporal usa o ano de depósito do pedido representante, escolhido como o mais antigo entre os membros recuperados na extração original.

| Janela do depósito | Treino | Validação | Teste | Total |
|---|---:|---:|---:|---:|
| 2010–2014 | 54 | 7 | 6 | 67 |
| 2015–2019 | 53 | 7 | 7 | 67 |
| 2020–2024 | 53 | 6 | 7 | 66 |
| Total | 160 | 20 | 20 | 200 |

A estratificação combina janela temporal e partição original. Dentro de cada estrato elegível, a seleção usa ordenação SHA-256 com semente 42. Uma família que era de treino, validação ou teste permanece na mesma partição. Os arquivos congelados e a auditoria permitem repetir exatamente a seleção. O script interrompe a execução quando o pacote ou uma saída congelada diverge do esperado.

A alocação entre janelas é quase uniforme, não proporcional ao universo. Não há estratificação por classe CPC ou idioma. Os 200 casos são uma subamostra de uma seleção prévia de 1.000 famílias; não constituem amostra representativa de todas as patentes com vínculo brasileiro. O histórico de uso da base em experimentos antigos não foi reconstituído integralmente. Preservar as partições evita transferir antigos exemplos de treino para o novo teste, mas não demonstra que o teste nunca tenha sido observado em trabalhos anteriores.

## Textos em português e inglês

O piloto contém 185 pares título/resumo pt/pt, 5 en/en, 9 pt/en e 1 en/pt. Idiomas diferentes no mesmo registro são permitidos e registrados por campo. Os idiomas são metadados herdados do PATSTAT; não são uma nova classificação automática.

O pré-processamento preserva os textos originais e gera uma cópia normalizada com Unicode NFC e quebras de linha padronizadas. Não remove acentos, não altera caixa, não elimina palavras técnicas e não traduz os textos antes da extração. Não há truncamento nesta etapa. O limite do tokenizador será tratado no momento da geração, com registro dos trechos efetivamente apresentados.

O JSON de saída mantém seis grupos — memes técnicos, pares de convergência, funções, materiais, processos e efeitos — com chaves estáveis em português e termos/evidências no idioma original. Evidências identificam o campo, o idioma e o intervalo `[inicio:fim]`, medido em pontos de código Unicode sobre o texto normalizado. O validador confere a correspondência literal e as referências entre IDs. Não se aceita evidência traduzida como citação literal.

Título e resumo foram selecionados separadamente entre membros da família na extração original. O pacote não conserva o pedido de origem de cada texto. O pré-processamento registra essa origem como desconhecida. `appln_id`, `appln_auth` e `appln_nr` identificam o pedido representante, não comprovam a origem dos textos. `appln_nr` não será renomeado para número de publicação. Uma correção dessa limitação exigirá nova consulta à fonte, com rastreamento por pedido/texto.

JSON inválido ou evidência inconsistente é falha de extração. Arrays vazios representam ausência de evidência somente em uma resposta válida. O retorno bruto do modelo deverá ser mantido na futura execução. Textos das patentes são dados: eventuais instruções dentro deles não integram o prompt do pesquisador.

## Supervisão CPC e alinhamento

O alvo herdado é o primeiro símbolo CPC da família em ordem alfanumérica, originalmente denominado `cpc_primary`. Neste protocolo ele se chama **`cpc_proxy`**. Não é uma anotação humana nem comprovação de CPC principal oficial. O símbolo integral é preservado, sem remapeamento silencioso para classe ou subclasse. Os CPCs não entram no prompt de extração; a supervisão fica em arquivos separados de treino, validação e teste.

Há forte dispersão de rótulos. O treino contém 142 CPCs proxy distintos em 160 famílias. Apenas 3/20 exemplos de validação e 3/20 de teste têm o mesmo rótulo integral observado no treino. O piloto permite testar a execução LoRA, mas acurácia exata nesse alvo exigirá interpretação cuidadosa. Uma avaliação hierárquica ou um alvo de subclasse seria uma decisão adicional de protocolo, a ser registrada antes do treino e sem alterar a amostra a partir dos resultados.

O alinhamento planejado usará o E5 multilíngue, mantendo os termos originais pt/en e o mapa entre variantes e conceitos. Semelhança vetorial deverá ser confirmada pelo contexto técnico antes de unir termos. A anotação humana independente deverá contemplar português, inglês e registros mistos, com os mesmos critérios de evidência. Ela ainda não foi produzida nesta etapa.

## Alcance dos indicadores e lacunas

| Lacuna ou diferença | Tratamento adotado | Consequência |
|---|---|---|
| Dados chineses substituídos por famílias com vínculo BR | Registrar adaptação de população e idioma | Comparação metodológica; valores não diretamente equivalentes |
| Fonte antiga inclui IPC C12Q | Filtrar ANY CPC A61/C12N disponível | Escopo atual verificável, com limitação de cobertura IPC |
| Textos de membros possivelmente distintos | Origem textual desconhecida explícita | Não inferir documento único nem disponibilidade histórica |
| Sem número/data de publicação | Não inventar esses campos | Avaliação com informação pública em cada corte permanece pendente |
| Sem histórico anterior a 2010 | “Primeira aparição observada no piloto” | Não afirmar novidade tecnológica histórica |
| Sem rede de citações datada | Não preencher Dh/NDCG com valores artificiais | Comparação bibliométrica depende de aquisição adicional |
| CPC proxy esparso | Preservar alvo e medir cobertura | Desempenho CPC não é medida direta da extração dos seis campos |
| Sem ouro humano para extração | Planejar anotação independente pt/en | Validade estrutural do JSON não demonstra correção semântica |
| GPU anterior sem BF16 e com 14,46 GiB livres | Manter diagnóstico e bloquear expectativa de treino BF16 nessa sessão | Treino real exige outra GPU ou protocolo QLoRA explicitamente aprovado |

As decisões sobre EDh, cortes por média, NDCG e a inconsistência da ablação permanecem registradas em `adotado.indices`. O piloto não elimina as lacunas matemáticas do artigo. Novidade, alinhamento e temas precisam ser avaliados com uma definição temporal consistente e sem usar o teste para ajustar o procedimento.

## Artefatos e validação

`experimento.json` separa o desenho publicado das decisões brasileiras. O seletor conserva o pacote e os splits; o pré-processador produz entradas de extração, metadados e supervisão CPC separados. O schema e o prompt são versionados. Os notebooks 00, 02 e 03 são executáveis em CPU no Colab; o 01 permanece um diagnóstico de GPU/modelos.

O conjunto desta entrega prepara os dados e contratos de extração. Treinamento real Qwen3-8B, geração, embeddings, alinhamento e métricas não são declarados executados. Os resultados de validação local são registrados separadamente em `docs/VALIDACAO_ENTREGA_BR.md`.

Referências documentais locais: artigo v1 em `dados/referencia/artigo_llm_eidt_v1.pdf`, notebook de origem preservado em `dados/referencia/02_extrair_1000_lora_patstat_origem.ipynb` e registro `dados/brutos/patstat_br_1000/proveniencia.json`.
