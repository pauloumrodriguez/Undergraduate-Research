# Revisão do teste QLoRA após falta de memória

O pesquisador enviou uma captura da execução do notebook04. O relatório exibido registra `memoria_gpu_insuficiente` e `etapa_falha=passo_de_treinamento_diagnostico`. O processo retornou código1 e a célula mostrou `CalledProcessError`. Essa última mensagem é a propagação da falha do programa chamado pelo notebook; a causa registrada pelo programa é falta de memória CUDA.

A captura foi obtida após o término do processo. O painel indicava 0,0/15,0 GB de RAM da GPU nesse momento. A liberação da memória após a saída do processo é compatível com esse valor; ele não mede o pico durante a operação que falhou. O saldo de unidades de computação e a disponibilidade futura do Colab são aspectos separados da capacidade de memória necessária para este passo. As regras de acesso e os limites de uso são dinâmicos, conforme o [FAQ oficial do Colab](https://research.google.com/colaboratory/faq.html#resource-limits).

A integração Google Drive não conseguiu recuperar o JSON completo. Em seguida, o pesquisador forneceu os campos de erro e parte da memória: a exceção `OutOfMemoryError` registrou uma tentativa de alocar 1,16 GiB com apenas 739,81 MiB livres em uma GPU de 14,56 GiB. O processo ocupava 13,84 GiB, com 13,22 GiB alocados pelo PyTorch e 501,89 MiB reservados mas não alocados. Após o carregamento, o PyTorch tinha 5,659 GiB alocados. Esses valores confirmam falta de memória durante o passo. A subfase exata não foi individualizada pela versão anterior. A sugestão genérica de configuração do alocador na mensagem não demonstra que fragmentação seja a causa principal.

## Alteração adotada para o próximo teste

O perfil adicional `br_patstat_200_qwen3_8b_qlora_nf4_fp16_smoke_v2_ctx1024` reduz o comprimento do tensor do teste de 2.048 para 1.024 posições. Os 160 exemplos de treino foram anteriormente medidos com o tokenizador real do Qwen3-8B e o mesmo prompt/alvo, resultando em 208–744 tokens. Assim, o novo limite mantém os textos completos e reduz o padding do teste de capacidade.

A hipótese é reduzir o uso de memória das ativações e dos logits ao diminuir o comprimento da sequência. O teste real na GPU continua necessário; a mudança não garante sucesso e não altera a quantidade de memória disponível no hardware.

São preservados Qwen3-8B, revisão de pesos/tokenizador, NF4 com quantização dupla, cálculo FP16, LoRA rank8 com q_proj/v_proj, microbatch1 e um passo diagnóstico. Não há alteração da amostra, do alvo CPC ou das partições. O perfil anterior permanece no projeto e o script aceita ambos, cada um com o seu limite explicitamente validado. A configuração base do experimento mantém seu hash.

## Artefatos e execução

O notebook04 atualizado usa `config/perfil_qlora_teste_1024.json`. O script registra separadamente forward, backward, verificação de gradientes e passo do otimizador, permitindo localizar melhor uma eventual nova falha. O resumo final mostra o motivo completo do erro, a fase e os picos de memória, além do caminho do relatório.

Atualize a pasta do Drive com a nova entrega. Para executar o04, são indispensáveis o próprio notebook, `scripts/testar_qlora_gpu.py`, o novo perfil1024 e o índice `SHA256SUMS.txt` da mesma entrega. Mantenha o arquivo de perfil anterior para rastreabilidade. Reabra o notebook atualizado e execute suas células com GPU. Os notebooks00–03 não precisam ser refeitos por esta alteração.

Se a sessão atual continua conectada e livre, ela pode ser usada para o novo teste, preservando o cache de pesos em `/content`. A criação de outra máquina pode exigir novo download. Não repetir automaticamente o perfil que falhou.

## Alcance da validação local

A revisão é verificável em CPU quanto aos perfis, hashes, tokenização, máscaras e controles de partição. A validação real do carregamento e do passo com 1.024 posições será realizada no Colab pelo pesquisador. Não se declara recuperação de memória ou treinamento bem-sucedido antes desse resultado.

A nova validação com o tokenizador real passou para os 160 exemplos com limite1.024, sem recorte. Cinco testes de compatibilidade e rejeição de perfis inconsistentes passaram. O resultado detalhado emCPU está em `resultados/etapa_1/piloto_br_200/validacao_tokenizador_qlora_1024_cpu.json`.
