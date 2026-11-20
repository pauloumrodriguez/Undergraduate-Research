# Extração estruturada e revisão humana — notebook 08

Protocolo v1, 5 de novembro de 2026. Adaptação brasileira do LLM-EIDT, sem alegação de reprodução numérica dos resultados chineses.

## Objetivo e população

Qualificar a extração de seis grupos: memes técnicos, pares em convergência, funções, materiais, processos e efeitos. A etapa usa seis famílias da partição de validação, duas por janela de depósito (2010–2014, 2015–2019, 2020–2024). Seleção pelos menores SHA-256 de `08|42|id_familia_docdb` em cada janela, sem consultar acertos CPC ou escolher exemplos favoráveis. IDs congelados no perfil.

As seis famílias permitem uma primeira revisão de custo manejável. Não representam o corpus brasileiro nem garantem cobertura dos idiomas, setores ou dificuldades. O perfil registra a seleção e as entradas preservam os idiomas. Não se extrai o conjunto de 200 automaticamente nesta entrega.

O teste CPC do 07 teve zero acertos completos em ambos os modelos, com formato sintático válido em 1/20 para a base e 20/20 para o adaptado. Isso não valida a qualidade da extração. O adaptador permanece o da época 3, selecionado pela perda de validação no 05. Nenhuma seleção usa os resultados de teste do 07.

## Procedimento congelado

- Qwen3-8B na revisão do projeto, NF4 com dupla quantização e cálculo FP16. Mesmo checkpoint, entradas, prompt, orçamento e decodificação para base e adaptador.
- Um modelo quantizado na GPU. `disable_adapter()` permite executar a base; não há mesclagem ou novo treinamento. Mantém o preparo dos pesos não quantizados empregado no 06/07.
- Usa o prompt `extracao_patstat_br.txt` e o schema `patstat-br-extracao-1.0` preparados no 03, sem modificar os arquivos congelados. O prompt recebe somente identificador, idiomas, título e resumo. Não recebe CPC, datas, classificação de novidade ou citações externas.
- Entrada até 2.048 tokens, incluindo instruções e template. Saída até 2.048 tokens; contexto máximo de 4.096. O orçamento de saída é ampliado frente aos 1.024 inicialmente planejados para acomodar seis listas e evidências. Não recorta nem traduz os textos e não impõe um número de itens por campo.
- Decodificação greedy, uma família por vez, sem thinking. Calcula logits apenas para o último token (`logits_to_keep=1`) para reduzir memória de geração. Não registra todos os scores do vocabulário.
- Nenhuma correção de JSON, remoção de cercas Markdown, ajuste de offsets, repetição corretiva ou escolha da melhor resposta. Preserva tokens e saída bruta. Resposta interrompida ou inválida não é ausência de evidência.

Referências técnicas: [Qwen3 / logits_to_keep](https://huggingface.co/docs/transformers/v4.57.1/model_doc/qwen3) e [PEFT / disable_adapter](https://huggingface.co/docs/peft/v0.18.0/en/package_reference/peft_model). As versões efetivas permanecem fixadas em requirements.txt e registradas por execução; a consulta documental não altera dependências.

## O que o programa valida

JSON estrito, sem chaves duplicadas nem NaN; schema completo; família e idiomas; IDs únicos; referências existentes; pares distintos sem repetição inversa; citações literais com offsets Unicode Python `[inicio:fim]`; coerência entre idioma do item e evidências. A geração deve terminar em EOS e não conter tokens especiais inesperados.

Uma resposta só recebe `extracao_validada` se cumprir todas essas condições. Campos inválidos recebem `null` nessa saída validada, mantendo a resposta bruta inteira para inspeção. Contagens de itens de uma resposta inválida ficam indisponíveis, nunca zero. As estatísticas automáticas têm denominador previsto de seis famílias por variante e mostram separadamente quantas terminaram. A conclusão do programa significa 12 tentativas de geração salvas, não 12 extrações corretas.

A presença literal de uma citação não prova que ela sustenta a interpretação, a integração técnica entre memes ou a categoria de efeito. Essas decisões exigem revisão humana. Listas vazias estruturalmente válidas também podem conter omissões.

## Execução no Colab

1. Copiar notebook 08, script `extrair_evidencias.py`, perfil `perfil_extracao_validacao6.json` e novo `SHA256SUMS.txt` para as subpastas correspondentes no Drive. Preservar todos os arquivos anteriores, o prompt, o schema e o checkpoint do 05.
2. Abrir o 08 em GPU e executar em ordem. O notebook confere hashes, origem, checkpoint, dependências e recursos. O cache dos pesos fica em `/content`, os resultados no Drive.
3. O programa cria uma pasta estável em `resultados/etapa_5/piloto_br_200/extracao_<hash-do-perfil>/`. Salva uma resposta por vez e um relatório de cada chamada. Pode retomar respostas existentes somente com mesmo código, perfil, prompt e ambiente registrado. Saídas inválidas concluídas também são reutilizadas.
4. Não executar duas sessões simultâneas. Se uma desconexão abrupta deixar a trava, encerrar a sessão antiga antes de habilitar a opção de liberação no notebook. Não apagar respostas para provocar nova geração. Mudança do ambiente é uma nova condição experimental: preservar o relatório e solicitar análise em vez de alterar os hashes.
5. Enviar resumo, `relatorio.json` e `extracoes.jsonl`. Preservar toda a pasta, inclusive `respostas/`, `execucao.json`, chamadas e prompts auditados. Falhas de infraestrutura permitem retomada das tentativas não salvas; devem permanecer registradas.

O contexto de extração é maior que o diagnóstico CPC. Os testes em CPU não garantem capacidade da T4; falta medir esta execução real. Se ocorrer falta de memória, enviar o relatório. Não há redução automática de contexto ou troca de modelo.

## Revisão humana independente

O programa fornece `anotacao_independente.jsonl`, com os textos originais, idiomas e campos pendentes. Fazer cópias para cada anotador, sem abrir previsões antes de registrar sua anotação inicial. Idealmente usar dois anotadores capazes de ler pt/en, com conhecimento técnico e um terceiro momento de adjudicação. Se houver apenas um anotador, registrar essa limitação e não alegar concordância entre avaliadores.

Para cada família:

1. Registrar anotador, data e os itens de cada um dos seis grupos, seguindo as definições e objetos do schema. O campo `anotacao` contém as seis listas; os dados de família e idiomas já estão no registro. `null` é pendente. Usar `[]` somente após revisar e concluir que não há evidência no texto fornecido. Marcar `revisao_concluida` ao terminar todos os grupos.
2. Memes são unidades técnicas centrais, como mecanismos, princípios ou componentes. Funções descrevem o que a tecnologia faz. Materiais identificam substâncias/materiais. Processos descrevem procedimentos ou sequências. Efeitos são resultados explicitados, com categoria `reducao_custos`, `ganho_eficiencia` ou `outro`; vantagem genérica não implica eficiência.
3. Pares exigem integração de dois memes sustentada pelo texto. Coocorrência não basta. Efeitos podem referenciar memes, funções, materiais ou processos existentes, apenas quando o texto sustenta o vínculo. Não inferir novidade histórica, disrupção ou impacto.
4. Copiar citações e identificar o campo de origem. Offsets são posições de caracteres Unicode, com fim exclusivo, sem mudar acentos/espaços. A versão inicial preserva a exigência de offsets do schema; erros nos números são registrados, não reparados silenciosamente. Guardar versões originais e adjudicadas separadamente.
5. Só depois de congelar a anotação independente, abrir uma cópia de `revisao_cega_modelos.csv`. Julgar suporte semântico, omissões, integração e efeitos. A coluna de erros automáticos é auxiliar. Não apresentar ao avaliador `chave_variantes_nao_enviar_ao_anotador.json`, os arquivos `respostas/` ou `extracoes.jsonl`, que identificam as variantes. A/B muda por família; o cegamento é operacional, não criptográfico, e o estilo da resposta pode revelar a variante.

## Correspondência e avaliação futura

Fixar a referência adjudicada antes de revelar A/B. Para termos, considerar correspondência quando representam o mesmo conceito técnico com mesmo papel e escopo no texto; não basta proximidade lexical. Evidências devem sustentar a interpretação, mas podem usar trechos literais diferentes. Pares correspondem quando os dois memes mapeados são os mesmos, sem considerar ordem, e a integração está sustentada. Efeitos exigem mesmo resultado técnico e categoria, com vínculos equivalentes quando expressos.

Mapear itens um a um por campo. Duplicatas não podem obter múltiplos créditos pelo mesmo item de referência. Registrar decisões ambíguas e adjudicação, incluindo sinônimos pt/en; não alterar regras após revelar qual modelo produziu o candidato. Julgar omissões consultando o texto integral e a referência independente.

Precisão, revocação e F1 dependem da anotação, ainda ausente. Não são calculados automaticamente no 08. Na análise posterior, relatar TP/FP/FN por campo e denominadores, cobertura de respostas completas e inválidas, e comparação pareada. Para uma análise ponta a ponta, uma extração rejeitada pelo validador não fornece itens aceitos e os itens de referência dessa família permanecem como FN; não excluí-la do conjunto. Separar eventual análise semântica das respostas brutas da análise estrita, explicitando o denominador.

## Condição para ampliar

Examinar as 12 respostas e as anotações, identificando problemas de instrução, JSON, offsets ou interpretação. Correções demonstráveis dão origem a uma nova versão do protocolo de desenvolvimento, conservando esta execução. Não escolher o modelo só por formato ou quantidade de itens. Depois de estabilizar o procedimento na validação, congelar uma avaliação de extração nas 20 famílias de teste com referência humana independente. Elas já foram usadas para avaliar CPC, fato que deve continuar explícito. Só então definir a aplicação às 200 famílias e o alinhamento E5. Este notebook não executa alinhamento, indicadores ou avaliação de impacto.

## Verificação da entrega

Oito testes em CPU verificaram seleção determinística, JSON estrito, Unicode, offsets, idiomas, referências, interrupção, integridade da retomada, origem local e compilação das células. O tokenizador real da revisão fixada mediu 1.230–1.659 tokens nos seis prompts, sem recortes. O checkpoint e a inferência NF4 real serão verificados no Colab; não foram executados localmente nesta entrega.

Um teste adicional com Qwen3/PEFT pequenos e aleatórios em CPU confirmou a API de geração com `logits_to_keep`, alternância de adaptadores e preservação dos pesos. Outro teste de integração, com GPU/modelo simulados, interrompeu a execução depois de duas respostas, retomou as dez faltantes e preservou uma saída inválida sem regenerá-la. Formulários humanos permaneceram intactos e uma chamada após a conclusão não gerou respostas novas. Esses testes não medem qualidade de extração nem memória da T4.
