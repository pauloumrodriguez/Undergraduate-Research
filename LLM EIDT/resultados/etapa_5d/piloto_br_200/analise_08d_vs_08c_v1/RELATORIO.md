# Resultado 08d comparado ao 08c

15/11/2026 · análise assistida · duas famílias de desenvolvimento

## Conclusão

O 08d resolveu as falhas de conclusão/estrutura nestes casos: oito chamadas concluídas, sem truncamento, e quatro fluxos válidos. A revisão semântica ainda encontra erros importantes. Não autoriza aplicar a extração às 200 famílias, executar o alinhamento ou selecionar adaptador para produção.

O modelo base recuperou mais itens da referência do que o adaptado nestas duas famílias. Isso não prova superioridade geral: a referência foi revisada depois de observar previsões, as regras foram desenvolvidas nos mesmos casos, e o treinamento do adaptador teve alvo CPC, não supervisão direta dos seis grupos. O resultado é compatível com ausência de benefício garantido do ajuste CPC para extração; não estabelece causa.

## Integridade e regra de comparação

Hashes dos dois JSONLs, script, núcleo, perfil e referência conferidos. As oito validações foram reproduzidas com o código congelado; quatro agregados e métricas técnicas conferem. O ambiente reportado é igual ao 08c (T4, Python 3.13.16, PyTorch 2.14.1+cu130 e mesmas versões inventariadas). A comparação não certifica igualdade de hardware/estado interno ou determinismo numérico absoluto.

A referência v2 mantém seus 14 itens, sem alteração. As regras são as mesmas da análise anterior: correspondência por conceito/papel/contexto, um a um e no mesmo grupo; preservação de operadores/alternativas; efeito com categoria e vínculos sustentados. Não se repararam respostas nem se adicionaram citações. Ausência de correspondência não é, por si só, invenção factual. Campos ausentes de referência podem indicar limites de cobertura ainda registrados.

## Métricas condicionais

| Versão / variante | Fluxos válidos | TP | FP operacional | FN | Precisão | Revocação | F1 condicional |
|---|---:|---:|---:|---:|---:|---:|---:|
| 08c / base | 0/2 | 0 | 0 | 14 | — | 0.0% | 0.0% |
| 08c / adaptado | 2/2 | 5 | 35 | 9 | 12.5% | 35.7% | 18.5% |
| 08d / base | 2/2 | 9 | 13 | 5 | 40.9% | 64.3% | 50.0% |
| 08d / adaptado | 2/2 | 6 | 29 | 8 | 17.1% | 42.9% | 24.5% |

TP: item correspondente; FP operacional: previsão sem correspondência sob a referência/regra atual; FN: item humano não recuperado integralmente. A melhora da base de 0 para 9 TPs inclui a passagem de fluxos rejeitados para fluxos válidos; não deve ser apresentada como ganho puramente semântico em saídas antes utilizáveis. As 16 observações parciais da base no 08c continuam fora da análise principal.

No 08d foram inspecionados 57 itens: 22 da base e 35 do adaptado. A base corresponde a 9 dos 14 itens; o adaptado a 6 dos 14. As correspondências são aplicação assistida da regra, ainda sem adjudicação independente. Não se calcula média macro nem significância com estes dois casos. A referência tem zero pares positivos: não permite estimar capacidade de detectar convergência verdadeira. Revocação de pares é indefinida, não zero.

## Melhorias observadas

- Base: nenhum meme nem processo indevido na família curta; reconhece composto e composição como materiais. Ambas as variantes preservam prevenção OU tratamento em uma unidade (alvo delimitado pela evidência), corrigindo a fragmentação do 08c.
- Ambas preservam “e/ou” na finalidade do resumo da família longa e distinguem substrato sólido de derivado marinho. O texto abreviado de uma função pode ser desambiguado pela evidência segundo a regra anterior; isso não permite mudar operador lógico ou acrescentar alternativa ausente.
- No adaptado, desapareceram “doenças” como material e “divulgação” como processo. Isso remove erros específicos, mas a lista de materiais da família curta ficou vazia: os três materiais da referência continuam não recuperados.
- O adaptado deixou de usar categorias de custo/eficiência nos efeitos destes casos. Entretanto continua duplicando finalidades como efeitos; mudar a categoria para “outro” não resolve isso.

## Problemas remanescentes

- Base classifica redução de adesão e prevenção de vascularização como redução de custos, e lisura como ganho de eficiência. Categorias e inferências não são sustentadas pelos textos.
- Adaptado continua criando memes a partir de propriedades e valores, além de métodos de caracterização usados apenas para controle, contrariando D1. Na família curta mantém termos genéricos como memes e atribui modulação da autofagia como função não explicitada do composto.
- Convergência: quatro pares da base e nove do adaptado sem suporte nos critérios adotados. Há parte–todo, objeto/propriedade, relação entre medidas, operações apenas enumeradas e métodos alternativos. Em particular, microscopia eletrônica OU força atômica não prova uso integrado.
- Ambos omitem o sal como material da família curta, a função de crescimento/restauração do título da longa e a medição de rugosidade como processo. A base omite conversão; o adaptado perde determinação da absorção (que recuperara no 08c).
- Adaptado menciona conversão, mas tanto termo quanto citação param antes de “otimizado”. O qualificador do estado de chegada está no trecho T002, que não foi citado. É recuperação parcial; não se acrescentou o trecho para obter acerto.
- Efeito terapêutico do adaptado: descrição se aproxima do resultado alegado, porém vincula uma função de modulação não sustentada; falha de objeto completo conforme a regra anterior. A base descreve “utilizado para”, tratado como finalidade nesta aplicação estrita, não como resultado de utilidade/eficácia.

## Incertezas preservadas

Os candidatos a memes “substrato sólido” e “processo para seleção” mantêm a ressalva de cobertura da referência registrada antes do 08d. Sua falta de correspondência não comprova erro semântico. O novo candidato de conversão tem também perda de qualificador/evidência. Nenhum foi acrescentado ao gabarito para favorecer uma variante.

A paráfrase “utilizado para prevenção ou tratamento de doenças” da base é um caso de fronteira: outro avaliador pode considerá-la equivalente à alegação de utilidade citada. Na análise principal não há crédito por duplicação de finalidade. Se apenas esse item recebesse crédito, a base teria TP=10, FP=12, FN=4 e F1=55,6%, em vez de 50,0%. É sensibilidade pontual não adotada, não intervalo de confiança; a saída e a justificativa estão disponíveis para revisão. Não se pede alteração automática da referência.

## Custo observado

08d: 880,53 segundos (14 min 41 s), pico alocado 10,107 GiB, reservado 12,562 GiB, sem falta de memória. 08c: 912,28 segundos, mas sete chamadas contra oito no 08d. Não interpretar esses tempos isolados como benchmark de velocidade. Saídas e comprimentos mudaram.

## Próximo passo recomendado

Não iniciar outro ciclo de prompt (08e) apenas para acertar estas duas famílias. Manter 08d e referência v2 congelados como condição de desenvolvimento e examinar os casos de fronteira com um anotador/colaborador, se disponível. A etapa seguinte útil é preparar referência humana para as quatro famílias restantes do piloto de validação de seis, antes de consultar novas previsões, e avaliar o mesmo 08d nas duas variantes sem escolher pela resposta mais favorável.

Essas quatro famílias já passaram por 08/08b; portanto não são teste virgem. Registrar qualquer exposição anterior dos anotadores. O propósito é verificar se as regras mantêm comportamento em textos não usados nesta revisão D1–D5. A avaliação final continua exigindo protocolo congelado e referência apropriada no conjunto reservado, com limitações de exposição registradas. O conjunto de duas famílias sem pares positivos é insuficiente para validar a etapa de convergência.

Esta entrega faz a análise; não cria novo notebook, não gera novas respostas e não exige GPU do usuário. As próximas fichas/execução de quatro famílias ainda precisam ser preparadas. Não avançar às 200 ou ao alinhamento com os resultados atuais.

## Arquivos

- RELATORIO.html: resumo, fontes, referência e inspeção item a item com evidências.
- comparacao_detalhada.json: 57 julgamentos, correspondências, 28 registros de cobertura (14 por variante), métricas por grupo/família e comparação congelada com 08c.
- originais/: os três arquivos recebidos, cópia exata da referência, métricas anteriores e protocolo v2. Nada foi sobrescrito.
- MANIFESTO_SHA256.txt: hashes da entrega.

Análise produzida pelo assistente de IA sobre documentos locais. Nenhuma alegação das patentes foi validada por conhecimento clínico/experimental externo; avalia-se suporte textual. Não houve nova consulta ao artigo ou PATSTAT.
