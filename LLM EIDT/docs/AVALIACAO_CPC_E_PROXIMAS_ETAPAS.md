# Notebook 06 — avaliação comparativa de CPC por geração

Protocolo registrado antes da primeira execução do 06, em 4 de novembro de 2026. Esta entrega implementa somente o diagnóstico de geração na validação. As etapas posteriores descritas abaixo ainda não são notebooks executáveis.

## Ponto de partida confirmado

Os dois relatórios do Colab recebidos do pesquisador correspondem aos nove hashes conferidos na entrega local do 05. O treinamento concluiu três épocas e 30 atualizações na Tesla T4, sem erro, com pico reservado de 12,605 GiB. A perda média por token de validação foi 4,373849 antes do treino, 0,968413 na época 1, 0,676274 na época 2 e 0,600219 na época 3. A escolha do checkpoint `passo_000030` segue o critério predefinido de menor perda de validação.

Não houve recorte nos 180 exemplos usados pelo treinamento/validação. O relatório informa que a partição teste não foi aberta. As cópias recebidas do relatório de treinamento e de preparação do ambiente são arquivadas em `resultados/etapa_2/piloto_br_200/` e vinculadas ao perfil 06 por SHA-256.

Os relatórios identificam o checkpoint; os arquivos de pesos continuam no Drive. O notebook 06 verificará o hash do manifesto e todos os arquivos nele declarados antes de carregar o adaptador. Não é necessário repetir o treinamento.

## Pergunta desta avaliação

Após a adaptação ao CPC proxy, o modelo passou a gerar mais códigos completos corretos nas 20 famílias de validação?

A perda anterior usa os tokens corretos precedentes da resposta durante sua avaliação. Na geração livre, o modelo recebe apenas título, resumo e idiomas e produz a resposta sem o CPC esperado. A taxa de acerto do código completo pode ser baixa mesmo com perda por token reduzida. Em 17 das 20 famílias de validação, o CPC integral não aparece no treino.

A validação já foi utilizada para escolher a época do adaptador. Portanto, o 06 é um diagnóstico de desenvolvimento, não uma estimativa independente do desempenho final. O alvo continua sendo o primeiro CPC integral alfanumérico herdado do pacote PATSTAT, sem equivalência a classificação principal oficial ou anotação dos seis campos de extração.

## Comparação congelada

| Item | Regra |
|---|---|
| Dados | Somente as 20 famílias do arquivo de validação congelado |
| Base | Qwen3-8B na revisão e quantização do treinamento, com o adaptador desativado temporariamente |
| Adaptado | Mesma instância da base, com o adaptador da época 3 habilitado |
| Precisão | NF4, double quant, cálculo FP16; preparação dos pesos não quantizados compatível com a do treino |
| Entrada | Mesmo prompt CPC do 05, título/resumo pt/en e idiomas; sem alvo CPC |
| Geração | Greedy, `do_sample=false`, um beam, sem modo thinking, até 32 tokens novos |
| Contexto | No máximo 992 tokens de entrada + 32 de saída; sem recorte automático |
| Lote | Uma família por vez; 20 respostas de cada variante, 40 no total |
| Treinamento | Nenhuma atualização de pesos; avaliação e modo de inferência |
| Repetições | Sem várias tentativas para escolher uma resposta favorável |

O programa usa `disable_adapter()` para obter a condição base e restaura o adaptador para a segunda condição, sem fundir pesos. A geração utiliza configuração explícita, em vez de herdar parâmetros de amostragem do modelo. Esses mecanismos são documentados em [PEFT 0.18 — modelos](https://huggingface.co/docs/peft/v0.18.0/en/package_reference/peft_model) e [Transformers 4.57 — geração](https://huggingface.co/docs/transformers/v4.57.1/en/main_classes/text_generation).

## Pontuação definida antes das respostas

**Métrica primária:** número e proporção de códigos CPC integrais corretos em 20 famílias, separadamente para base e adaptado. Para contar como acerto, a resposta deve terminar no marcador EOS e coincidir integralmente com o alvo depois da normalização definida abaixo.

**Normalização:** Unicode NFC, conversão para maiúsculas e remoção de espaços. Não remover zeros, não mudar números, não retirar trechos explicativos, não remover blocos de raciocínio ou cercas Markdown e não procurar o primeiro código dentro de uma resposta longa. Remover apenas o token terminal EOS antes de avaliar o conteúdo textual gerado; preservar a sequência bruta no registro.

**Formato sintático:** correspondência completa com `[A-HY][0-9]{2}[A-Z][0-9]{1,4}/[0-9]{2,6}` após normalização. Essa expressão verifica somente a forma do símbolo, não sua existência no catálogo CPC nem sua pertinência à patente. Não atualizar os alvos históricos com uma edição atual da classificação.

**Métricas secundárias:** proporção com formato compatível, proporção encerrada em EOS, quantidade interrompida no limite de geração e comparação pareada (ambos corretos, somente base correta, somente adaptado correto, ambos incorretos). O denominador permanece 20: saídas inválidas e sem EOS não são excluídas para melhorar a taxa de acerto. Os resultados das duas variantes são comparados sobre as mesmas famílias.

Erros de execução, falta de memória ou interrupção produzem relatório de falha e saídas parciais. Não apresentar métricas finais enquanto as 40 gerações não estiverem completas. Uma nova execução tem pasta própria; não completar silenciosamente um relatório antigo com parâmetros diferentes.

## Como executar no Colab

1. Atualizar as subpastas correspondentes no Drive com `notebooks/06_avaliar_cpc_validacao.ipynb`, `scripts/avaliar_cpc_geracao.py`, `config/perfil_avaliacao_cpc_validacao.json` e `SHA256SUMS.txt`.
2. Manter os dois helpers do 05, os dados congelados, requisitos, relatórios e a pasta inteira do checkpoint no Drive. O notebook confere suas versões e aponta precisamente um arquivo ausente ou divergente.
3. Abrir o 06 com GPU, conferir a raiz `/content/drive/MyDrive/Replicação LLM EIDT IC` e executar as células em ordem. Não é necessário repetir 00–05. O cache local de pesos pode ser reaproveitado se a sessão ainda o conservar.
4. Guardar o resumo final e enviar o relatório JSON e a tabela comparativa indicados ao final. As respostas brutas também ficam salvas no Drive. Não enviar os pesos do adaptador pelo chat.

O programa grava uma nova pasta de execução em `resultados/etapa_3/piloto_br_200/`, com relatório, saídas por família e tabela comparativa. O arquivo de preparação do notebook fica no mesmo diretório de resultados da etapa. A verificação local desta entrega usa CPU, tokenizador real e modelos pequenos sintéticos; não executa a avaliação Qwen3-8B no Colab.

## Sequência após o 06

### 07 — avaliação final CPC no teste reservado

Revisar os resultados do 06 e resolver eventuais defeitos de implementação usando treino/validação. Congelar prompt, normalização, limites, métricas e checkpoint antes de abrir o teste. Então comparar base e adaptado nas 20 famílias de teste, preservando todas as respostas e relatando contagens e limitações da amostra pequena. Não escolher outra época, seed ou prompt a partir dos resultados de teste. Uma correção necessária depois dessa abertura deve ser explicitada; o conjunto deixa de ser uma avaliação intocada para escolhas subsequentes.

### 08 — extração estruturada e validação humana

Preparar a extração dos seis grupos previstos: memes técnicos, convergências, funções, materiais, processos e efeitos. Reutilizar o schema pt/en e exigir evidências literais do título/resumo. Começar com um teste operacional em exemplos de treino; fixar o procedimento antes da avaliação reservada. Comparar base e adaptado porque o fine-tuning CPC não garante ganho na extração.

Preparar um formulário de anotação e critérios de evidência, ausência e erro. Usar revisão independente, preferencialmente sem revelar a variante que gerou cada resposta. JSON válido é uma checagem estrutural; a correção semântica requer anotação. Depois da validação do procedimento, executar o extrator congelado nas 200 famílias. Manter falhas de JSON/interrupções distintas de ausência de evidência.

### 09 — embeddings e alinhamento

Executar o encoder `intfloat/multilingual-e5-large` na revisão já registrada, em sessão separada do Qwen. Registrar convenções de prefixo, normalização, similaridade e critérios de alinhamento antes de aplicar à amostra completa. Validar pares de equivalência e ambiguidades com exemplos anotados; decidir limiares sem consultar o teste reservado. Preservar termos originais, vetores, decisões e proveniência.

### 10 — redes, indicadores e análise científica

Construir relações entre os elementos extraídos/alinhados e aplicar as definições matemáticas auditadas do estudo, mantendo explícitas as adaptações. Controlar a ordem temporal: uma patente não pode ter sua novidade julgada usando informação futura indisponível no momento pertinente.

O piloto de 200 famílias não substitui automaticamente o corpus histórico do artigo. O pacote disponível não conserva datas de publicação, rede de citações, edição PATSTAT ou o identificador de origem de cada texto. Métricas que dependam desses insumos exigirão dados adicionais; até lá, limitar os resultados às análises exploratórias sustentadas pelos dados presentes. Documentar sensibilidade à amostra, raridade dos CPCs e decisões metodológicas, sem atribuir à adaptação brasileira os resultados numéricos do estudo chinês.
