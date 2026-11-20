# Verificação da entrega 06

Data: 4 de novembro de 2026. Escopo: avaliação CPC por geração livre nas 20 famílias de validação, comparando base e adaptador fixado após o treinamento 05.

## Integridade e testes do programa

O programa é importável sem PyTorch. O préflight verifica hashes de configuração, fontes e relatórios, seleção da melhor época, manifesto e inventário do checkpoint, progresso e configuração LoRA. O teste automatizado de préflight usa um checkpoint sintético identificado apenas como fixture de software. Nenhum checkpoint sintético substitui os pesos reais esperados no Drive.

Oito testes do programa passaram em CPU, incluindo:

- Construção de prompt independente do alvo e rejeição de entrada longa sem recorte automático.
- Normalização conservadora, exigência de EOS para acerto e rejeição de texto extra ou múltiplos códigos.
- Métricas com denominadores fixos, comparação pareada e rejeição de predições duplicadas ou avaliação incompleta.
- Préflight com arquivos de treino e teste ausentes e abertura desses caminhos proibida no teste.
- Rejeição de dados/checkpoints com hash divergente, relatório de falha sem métricas finais e proteção de células CSV contra interpretação como fórmula.

## Teste PEFT real com modelo pequeno

Um Qwen3 pequeno inicializado aleatoriamente foi exercitado com LoRA não nulo e três prompts sintéticos. Logits e gerações com `disable_adapter()` coincidiram com os da instância base limpa; reabilitar o adaptador restaurou a condição adaptada, e recarregá-lo preservou as respostas. Nenhum peso mudou e nenhuma fusão foi realizada.

Registro: `resultados/etapa_3/piloto_br_200/validacao_peft_avaliacao06_cpu.json`. Esse teste confirma o mecanismo de alternância de adaptadores em CPU, sem quantização NF4 ou GPU. O programa recongela os parâmetros após sair do contexto `disable_adapter()`, pois a API pode reativar `requires_grad` nessa saída.

## Tokenizador real e notebook

O tokenizador da revisão Qwen3-8B congelada é usado na auditoria das 20 entradas reais de validação. São conferidos igualdade com o prefixo do prompt usado no 05, ausência de continuação supervisionada na entrada da geração, independência do alvo e respeito ao limite de 992 tokens mais 32 de resposta. Registro: `resultados/etapa_3/piloto_br_200/validacao_tokenizador_avaliacao06_cpu.json`.

O notebook tem 12 células, IDs únicos, UTF-8, código compilável e nenhuma saída antiga. As chamadas CLI e chaves de resumo correspondem ao programa. A preparação foi exercitada em CPU com arquivos de origem e retorno CLI simulado, sem carregar modelo; divergências de hash impedem a chamada, e falha de checkpoint é persistida no relatório. As assinaturas finais do perfil e programa são inseridas antes da instalação.

## Limite da entrega

Não foi executada localmente a avaliação Qwen3-8B das patentes em GPU. A existência e a integridade dos pesos reais no Drive serão conferidas pelo notebook antes do carregamento. Os testes de CPU não garantem memória, tempo ou respostas na Tesla T4. Nenhum resultado de acurácia foi inventado; os resultados experimentais serão produzidos ao executar o 06 no Colab.
