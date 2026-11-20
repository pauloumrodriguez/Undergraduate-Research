# Revisão 08b: citações compartilhadas e localização determinística

Protocolo 2.0 — 5 de novembro de 2026. Revisão de desenvolvimento na validação, sem novo treinamento e sem modificar os resultados anteriores.

## Motivação observada

O 08 terminou 12 gerações em aproximadamente 58,4 minutos na T4, sem erro de GPU. Sete respostas atingiram o limite de 2.048 tokens. Nas cinco respostas com schema válido, todas as 58 posições de evidências estavam incorretas: 55 citações existiam literalmente no campo indicado e três não existiam literalmente. A análise foi feita somente sobre os cinco JSONs completos; não houve recuperação parcial das sete respostas truncadas.

Isso justifica retirar do modelo a tarefa de contar caracteres e reduzir a repetição de citações. Não demonstra que as 55 citações sustentam semanticamente os itens, nem qual modelo é melhor. A verificação semântica permanece humana.

## Mudanças e justificativas

1. **Banco compartilhado de evidências.** O formato de geração `patstat-br-extracao-2.0` inclui uma lista `evidencias` com ID, campo de origem e citação literal. Os seis grupos referenciam esses IDs. Uma citação pode sustentar vários itens sem ser escrita várias vezes. As definições dos seis grupos permanecem as do projeto.
2. **Posições calculadas pelo programa.** Para cada citação, buscar todas as ocorrências exatas no campo indicado, inclusive sobrepostas. Não mudar caixa, acentos, espaços, pontuação ou grafia. Se houver uma ocorrência, atribuir início/fim Unicode e o idioma registrado para esse campo. Se houver zero ou mais de uma ocorrência, sinalizar ausência/ambiguidade e rejeitar a extração para uso automático. Não selecionar a primeira ocorrência silenciosamente. O prompt pede um trecho suficientemente contextualizado para identificação única.
3. **Formato compacto e saída de até 3.072 tokens.** Mantém até 2.048 tokens de entrada, sem recortes, e eleva o contexto máximo a 5.120. O banco e a instrução de JSON sem indentação visam reduzir tokens; o limite adicional é uma reserva, não garantia contra truncamento. Não limita artificialmente o número de itens nem pede omissões para caber. O custo e a memória reais devem ser medidos.
4. **Instrução sobre unidades técnicas.** Evitar duplicatas e expressões genéricas que não constituam conceitos técnicos. Coocorrência ainda não prova convergência. Não inserir conhecimento externo nem decidir novidade/disrupção.

Prompt, representação e orçamento mudam juntos. Uma diferença entre 08 e 08b não permite atribuição causal isolada a cada mudança. Dentro do 08b, base e adaptador usam exatamente os mesmos dados, prompt, formato, orçamento e decodificação. São decisões da adaptação brasileira, não especificações adicionais atribuídas ao artigo.

## O que permanece fixo

Mesmas seis famílias de validação e estratos, mesma revisão Qwen3-8B, quantização NF4/FP16, checkpoint da época 3 e módulos LoRA. Seleção por hash independente dos resultados CPC e das previsões. Doze gerações, uma por variante e família. Não abrir novas famílias de teste, selecionar outro checkpoint ou retreinar.

Os perfis, prompts, schemas e resultados 00–08 permanecem intactos. O 08b depende dos scripts e configurações anteriores para conferir o checkpoint. Não apagar arquivos antigos do Drive.

## Validação e rastreabilidade

Preservar a resposta bruta, tokens, schema de geração, hash do prompt, flags de término e erros. Validar JSON estrito, chaves, IDs, referências e a lista de citações. Registrar `localizacao_citacoes` com estado `localizada_unica`, `ausente` ou `ambigua` e as posições encontradas.

Somente quando a resposta está completa, sem erros de referência/localização, expandir as evidências e validar um objeto no schema 1.0. Esse objeto normalizado aparece em `extracao_validada` e é apropriado ao processamento posterior, ainda sujeito à revisão semântica. A resposta bruta 2.0 nunca é substituída pelo objeto normalizado. IDs dos itens, termos, descrições, categorias e vínculos não são corrigidos.

`schema_valido` mede o formato de geração 2.0; `estrutura_e_evidencias_validas` mede a normalização completa e a validação pelo schema 1.0. Esses valores não são precisão ou F1. Uma resposta truncada, com citação inexistente ou ambígua permanece uma falha, não uma ausência de informação. Listas vazias podem conter omissões semânticas, mesmo passando na validação.

Não há reparação de JSON, retirada de Markdown, correspondência aproximada, tradução de citações ou regeneração automática de respostas inválidas. O 08 não será reclassificado retroativamente como aprovado pelo novo procedimento.

## Executar e retomar

Copiar estes arquivos para as subpastas correspondentes no Drive:

- `notebooks/08b_extrair_evidencias_piloto.ipynb`
- `scripts/extrair_evidencias_v2.py`
- `config/perfil_extracao_validacao6_v2.json`
- `prompts/extracao_patstat_br_v2.txt`
- `schemas/extracao_patstat_br_v2.schema.json`
- `SHA256SUMS.txt` atualizado (substituir o índice anterior)

Copiar também este guia para `docs/`, se desejar consultá-lo no Drive. Abrir somente o novo 08b no Colab com GPU e executar em ordem. Não repetir 00–08. O notebook confere versões, hashes e checkpoint antes da geração. Os pesos usam cache temporário no Colab; as respostas ficam no Drive em `resultados/etapa_5b/piloto_br_200/extracao_<hash-do-perfil>/`.

Cada resposta é salva separadamente. Uma retomada com o mesmo perfil, script e ambiente reutiliza todas as respostas concluídas, válidas ou inválidas, e gera apenas as faltantes. Se houver desconexão abrupta, encerre a sessão anterior antes de liberar a trava residual. Nunca execute duas sessões simultâneas. Não altere hashes ou apague respostas para forçar uma nova tentativa.

Ao terminar, enviar resumo, `relatorio.json` e `extracoes.jsonl` da nova pasta de etapa_5b. Preservar os arquivos completos, incluindo chamadas, prompts e respostas individuais. Se houver falta de memória ou mudança do ambiente na retomada, preservar o relatório para análise; os limites não são reduzidos automaticamente.

## Revisão humana e próximos passos

Anotar textos antes de olhar previsões. Se já houver anotação independente congelada do 08, preservá-la e reutilizá-la, pois as famílias/textos são os mesmos. Se as previsões já tiverem sido vistas pelo anotador, registrar essa exposição; não alegar anotação independente cega. Quando possível, usar dois anotadores e adjudicação. Um único anotador não permite estimar concordância entre avaliadores.

O formulário `anotacao_independente.jsonl` continua usando os seis grupos da representação canônica. `null` indica pendente e `[]` ausência após revisão. Cada anotador trabalha em uma cópia, com identidade/data e estado de conclusão. Após congelar a referência, revisar uma cópia de `revisao_cega_modelos.csv`. A chave A/B e arquivos que mostram as variantes ficam separados dos materiais enviados aos avaliadores. O cegamento é operacional, não criptográfico, e o estilo de saída pode revelar o modelo.

Aplicar as regras de correspondência e adjudicação descritas em `EXTRACAO_E_REVISAO_08.md`: um a um por campo, equivalência técnica contextual, pares sem ordem e efeitos com categoria/vínculo sustentados. Citações podem ser literalmente diferentes e sustentar o mesmo conceito. Não dar crédito só pela presença do trecho nem selecionar modelo pelo número de itens.

Não ampliar às 200 famílias nem iniciar alinhamento apenas porque o JSON passou. Após analisar resultados e revisão humana, estabilizar o procedimento de extração e congelar sua avaliação nas famílias reservadas. Relatar que elas já foram avaliadas na tarefa CPC. A eventual escolha de base/adaptador deve usar validação de extração, nunca ajuste pelos resultados do teste.

## Verificação local

Sete testes em CPU verificam busca exata Unicode, ocorrências sobrepostas, ausência e ambiguidade, compartilhamento e campo de origem, JSON estrito, schema, referências, rejeição de saídas incompletas, integridade de retomada, seleção congelada, hashes e compilação das células. O tokenizador real mediu 1.222–1.651 tokens nos seis prompts, sem recortes. Testes adicionais cobrem a retomada integrada com interrupção simulada e a API de geração em Qwen3/PEFT pequenos reais em CPU.

Esses testes não medem desempenho da extração nem memória do Qwen3-8B NF4 nesta nova condição. A execução real de 08b na T4 permanece pendente no Colab.
