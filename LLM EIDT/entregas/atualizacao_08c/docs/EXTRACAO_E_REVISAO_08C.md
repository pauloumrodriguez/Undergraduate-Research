# Protocolo 08c — extração em etapas com JSON guiado

Versão 3.0, 5 de novembro de 2026. Teste de engenharia na validação da adaptação brasileira LLM-EIDT. Não é avaliação final, não treina outro adaptador e não altera resultados de 08/08b.

## Problema observado e objetivo

O 08b executou 12 chamadas em aproximadamente 74,2 minutos, sem falta de memória. Cinco saídas eram JSON interpretável, mas todas omitiram `pares_convergencia`; uma também usou um campo de origem inválido. O adaptador apresentou repetição de citações e de zeros. Nenhuma extração foi aprovada. JSON completo, citação localizada e correção semântica são critérios distintos.

O 08c altera o procedimento para diagnosticar esses problemas com menor orçamento total. São duas famílias da mesma validação: a de menor e a de maior soma de caracteres Unicode de título e resumo, com desempate por ID crescente. IDs: 68698300 (407 caracteres) e 50390156 (1.984 caracteres). A seleção usa comprimento, não acerto ou qualidade das previsões. A amostra cobre extremos de comprimento dentro das seis famílias, sem representatividade estatística.

## Etapas e comparação

Cada família é processada pelo modelo base e pelo adaptador da época 3. Revisão Qwen3-8B, checkpoint, NF4/FP16 e semente permanecem fixos.

1. **Elementos:** quatro listas obrigatórias — memes_tecnicos, funcoes, materiais, processos. Cada item fornece termo, idioma e IDs dos trechos de suporte. IDs dos itens são atribuídos pelo programa de acordo com grupo/ordem de saída, sem alterar seu conteúdo.
2. **Relações e efeitos:** duas listas obrigatórias — pares_convergencia e efeitos. Recebe os mesmos trechos e os elementos válidos da própria variante. As referências permitidas são construídas a partir desses elementos. Uma falha no primeiro estágio bloqueia o segundo daquele par família/modelo e é registrada como falha do pipeline, não como lista vazia.

Há quatro pipelines e no máximo oito gerações. Cada chamada usa até 3.072 tokens de entrada e 1.024 de saída, geração greedy, sem thinking. Não recorta a entrada. O máximo agregado de saída é 8.192 tokens, frente aos 36.864 possíveis no 08b; isso não garante uma proporção fixa de redução de tempo, porque há preparação de gramática, prompts e carregamento.

As duas variantes têm o mesmo procedimento e orçamento. As entradas do segundo estágio podem diferir porque dependem dos elementos da própria variante: a comparação é do pipeline completo. Não interpretar como experimento de relações com candidatos idênticos.

## Evidências identificadas pelo programa

Dividir separadamente título e resumo em trechos consecutivos de até 256 caracteres, preferindo cortar em espaço na segunda metade da janela. IDs T001… e R001… identificam campo, idioma, texto literal e intervalo Unicode Python `[inicio:fim]`. Concatenação dos trechos de cada campo deve reproduzir exatamente o original, sem remover espaços ou pontuação.

O modelo recebe todos os trechos em ordem, sem recortar ou resumir o texto. Cita somente os IDs, que são enumerados no schema. Não precisa reescrever citações ou calcular posições. Um corte pode dividir uma expressão ou relação: o prompt permite citar os dois trechos adjacentes. Esse particionamento não é segmentação linguística perfeita; os trechos podem incluir conteúdo irrelevante para um item. A referência a um trecho real não comprova que ele sustenta a interpretação, sobretudo em negações ou relações técnicas.

O objeto final válido é convertido para o schema canônico 1.0, usando as evidências literais dos trechos. A montagem não preenche grupos omitidos: só ocorre depois de validar todas as chaves exigidas nos dois estágios. Resultados parciais e gerações brutas continuam preservados separadamente.

## Controle da geração

Usa **lm-format-enforcer 0.11.3**, com integração `prefix_allowed_tokens_fn` do Transformers. A biblioteca restringe os próximos tokens conforme o schema. Especificamos chaves obrigatórias, ausência de propriedades extras e enums dos IDs de evidência/elementos. Mantemos uma validação independente ao final para JSON estrito, duplicatas, idiomas, pares, referências e schema canônico.

Configuração explícita da gramática: ordem das chaves fixada, no máximo um caractere de espaço consecutivo e teto técnico de arrays de 1.024 itens. O teto de arrays excede a capacidade útil de uma saída de 1.024 tokens, evitando o padrão implícito de 20 itens da biblioteca sem impor uma cota científica de achados. O alfabeto inclui caracteres latinos acentuados e os caracteres imprimíveis do prompt, para não restringir a geração a ASCII. Não se aplica penalidade de repetição que altere silenciosamente termos necessários.

Uma sequência dos últimos 32 tokens repetida três vezes provoca parada antecipada e invalidação, mesmo que o JSON parcial seja interpretável. É um detector técnico conservador de repetição, não um julgamento semântico; pode deixar passar outras repetições. Não corrige ou remove conteúdo repetido e não faz nova tentativa automática. EOS só é admissível após o fechamento permitido pela gramática, mas o orçamento ou uma interrupção ainda podem terminar antes de haver JSON completo. Controle de formato não garante término, cobertura ou veracidade.

Fonte técnica: [LM Format Enforcer — documentação e integração Transformers](https://github.com/noamgat/lm-format-enforcer). A versão usada está fixada no arquivo de requisitos próprio; a documentação consultada não autoriza atualização automática da biblioteca.

## Dependências e arquivos

O requirements.txt original permanece intacto. O novo `requirements_extracao08c.txt` conserva suas versões e acrescenta lm-format-enforcer 0.11.3 e interegular 0.3.3. O notebook protege PyTorch e NumPy nativos do Colab. Pydantic, exigido pela biblioteca, é inventariado na execução e entra no controle de retomada; a verificação local usou Pydantic 2.14.3. Não alegamos equivalência de ambientes diferentes.

Atualizar notebook 08c, script v3, perfil v3, os dois prompts v3, templates de schema, requirements_extracao08c.txt e SHA256SUMS.txt. Preservar todos os arquivos anteriores e o checkpoint do 05. O pacote ZIP de atualização contém esses arquivos e este guia; extrair e copiar seu conteúdo para as subpastas do projeto no Drive. Apenas enviar o ZIP ou apenas o notebook não instala as dependências do projeto.

## Execução, retomada e resultados

Abrir 08c no Colab com GPU e executar em ordem. Conferir hashes, seleção, checkpoint, instalação e recursos antes da geração. A preparação da gramática/tokenizador pode levar algum tempo antes da primeira chamada. Os pesos ficam no cache temporário do Colab; os resultados ficam em `resultados/etapa_5c/piloto_br_200/extracao_<hash-do-perfil>/`.

Salvar cada tentativa por família/variante/estágio, com hash de prompt/schema, tokens, resposta bruta, flags e validação. Retomar somente com mesmo código, perfil e ambiente registrado. Reutilizar tentativas concluídas, inclusive inválidas; não selecionar uma nova tentativa com resultado melhor. Se uma chamada falhar antes de ser salva, a retomada pode repeti-la, preservando o relatório da interrupção. Não rodar duas sessões simultâneas. Remover trava residual somente após encerrar a sessão anterior.

Arquivos principais:

- `relatorio.json`: estado, contagens por variante, chamadas, relações bloqueadas, memória, ambiente e hashes.
- `extracoes.jsonl`: quatro registros, um por família/variante, com estado de cada estágio e extração final quando válida.
- `geracoes.jsonl`: saídas brutas e validações de até oito chamadas. Enviar este arquivo também, pois o agregado não contém todo o texto gerado.
- `trechos/`, `prompts/` e `respostas/`: rastreabilidade integral e persistência para retomada.
- `anotacao_independente.jsonl`, `revisao_cega_modelos.csv` e chave A/B separada: preparação de revisão humana. Trabalhar em cópias e não alterar registros de geração.

O estado `extracao08c_concluida_revisao_pendente` significa que os quatro pipelines foram processados, podendo incluir falhas e relações bloqueadas. Não significa sucesso de qualidade. Não preencher `null` de extrações rejeitadas com listas vazias.

## Avaliação humana e limites

Preservar referência humana independente já produzida para essas famílias. Se ainda não existe, anotar os textos antes de ver as previsões, idealmente com dois avaliadores e adjudicação. Registrar exposição prévia às previsões. Não enviar a chave A/B aos anotadores durante revisão cega. Regras de correspondência por conceito/contexto, pares sem ordem, categoria/vínculo de efeitos e contagem um a um permanecem no guia do 08. Uma única pessoa não permite estimar concordância entre avaliadores.

Formato obrigatório e evidência existente são verificações técnicas. Não escolher modelo pela quantidade de elementos ou pela validade de JSON. O 08c não calcula F1 sem referência humana, não comprova ganho do LoRA, não amplia para 200, não executa alinhamento e não estabelece novidade histórica. Múltiplos componentes mudaram desde 08b, impedindo atribuição causal isolada. Usar este diagnóstico para decidir se é possível estabilizar a extração antes da avaliação reservada e ampliação.

## Validação local

Sete testes em CPU cobrem preservação Unicode dos trechos, seleção por comprimento, referências, validação de estágios, campos obrigatórios, JSON inválido, bloqueio de EOS antecipado pela gramática, detector de repetição e integridade de retomada. O filtro de tokens foi testado com o tokenizador real da revisão Qwen3-8B, incluindo termos acentuados e rejeição do fechamento prematuro do objeto.

Prompts medidos: 963–1.774 tokens, sem recorte; para o estágio de relações, essa medição usa elementos vazios de controle, não previsões reais. O programa mede novamente o prompt com os elementos gerados e interrompe se exceder 3.072 tokens.

Um teste integrado simulou interrupção depois de duas tentativas salvas, retomou sem regenerá-las e verificou que falha em elementos impede a chamada de relações. Outro executou a API real de geração com Qwen3/PEFT pequenos e aleatórios, tokenizador Qwen real e gramática real em CPU, conduzindo respostas sintéticas sem remover a máscara de tokens. Esses testes verificam integração e preservação dos pesos; não medem qualidade de extração nem execução NF4/T4. O teste real do 08c no Colab continua pendente.
