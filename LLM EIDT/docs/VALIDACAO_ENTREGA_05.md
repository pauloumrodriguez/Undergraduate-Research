# Conferência da entrega do notebook 05

Data: 4 de novembro de 2026. Escopo: programa, notebook e perfil de treinamento QLoRA CPC do piloto brasileiro. O treinamento Qwen3-8B completo ainda será executado no Colab.

## Arquivos e pré-condições

Os 37 arquivos do índice anterior no Desktop foram conferidos e não apresentaram divergências. A entrega adiciona o notebook 05, seu programa, perfil, documentação e registros de validação; o README e o índice são atualizados com cópias de segurança. O helper usado pelo diagnóstico 04b permanece byte a byte igual. O experimento base, a amostra e os dados de entrada mantêm seus hashes.

O notebook tem 12 células, código compilável, identificadores únicos, nenhuma saída antiga e assinaturas explícitas do programa e do perfil. Sua preparação foi exercitada em CPU com uma cópia temporária dos arquivos e um diagnóstico sintético identificado como fixture. O arquivo de teste estava ausente, e a preparação funcionou. Resumo de chat sem perfil completo, diagnóstico de falha e entrada com hash divergente foram rejeitados. Nenhum diagnóstico sintético foi instalado como evidência de execução GPU.

## Tokenização real dos dados

Usado o tokenizador da revisão Qwen3-8B congelada, sem baixar pesos ou executar o modelo:

| Partição | Famílias | Tokens por exemplo | Recortes | Tokens supervisionados totais |
|---|---:|---:|---:|---:|
| Treino | 160 | 208–744 | 0 | 1.984 |
| Validação | 20 | 181–699 | 0 | 244 |

Confirmadas máscaras somente sobre CPC+EOS e famílias disjuntas. O arquivo de teste não foi aberto por essa validação. Registro: `resultados/etapa_2/piloto_br_200/validacao_tokenizador_treino05_cpu.json`.

## Testes de treinamento em CPU

Nove testes passaram com PyTorch 2.9.1+cpu instalado em uma pasta isolada de verificação, sem alterar requisitos do Colab:

- A acumulação ponderada por tokens produz a mesma atualização que o lote efetivo em um modelo pequeno, com scaler aplicado no limite do grupo.
- A perda de validação é ponderada corretamente e restaura o modo de treinamento.
- Gradientes não finitos impedem a atualização do otimizador.
- A retomada conserva dropout, AdamW, scaler, geradores aleatórios e continuação dos pesos.
- Checkpoints incompletos, corrompidos ou incompatíveis são rejeitados antes da restauração.
- O cursor não pula a validação de fim de época, e empate favorece a primeira época treinada.
- A ordenação cobre cada exemplo uma vez por época e os erros persistem em relatório.

O teste adicional com uma arquitetura Qwen3 minúscula inicializada aleatoriamente e PEFT reais está documentado no arquivo `resultados/etapa_2/piloto_br_200/validacao_peft_checkpoint_cpu.json`. Ele compara retomadas nas atualizações 5, 10 e 30 com a continuação integral, incluindo as fronteiras de época. Os exemplos desse teste de software são sintéticos e não entram no piloto de patentes.

## Limites da verificação

Esses testes não executam Qwen3-8B, NF4/bitsandbytes, AMP FP16 em CUDA, nem confirmam memória ou duração de três épocas no Colab. A evidência de GPU existente é o resumo aprovado do 04b informado pelo pesquisador; o notebook 05 exige seu JSON completo no Drive. A validação em CPU não substitui a execução experimental nem comprova qualidade científica dos resultados.

Para retomar no Colab, o programa exige compatibilidade de código, perfil, dados, diagnóstico, versões e identificação da GPU. A igualdade bit a bit observada nos testes CPU não é prometida para diferentes kernels CUDA. Preserve as pastas de todas as sessões pertencentes à mesma retomada, pois o melhor adaptador pode estar em um checkpoint de uma sessão anterior.
