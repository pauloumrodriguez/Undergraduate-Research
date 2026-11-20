# Teste de capacidade QLoRA do piloto brasileiro

O pesquisador concluiu os notebooks 02 e 03 no Colab. O relatório de seleção enviado foi comparado à auditoria local e os cinco hashes dos arquivos pré-processados coincidem com a entrega congelada. Foram confirmadas 200 famílias, divisão 160/20/20, janelas 67/67/66 e nenhum título ou resumo vazio. O registro dessa conferência está em `resultados/etapa_1/piloto_br_200/conferencia_colab_02_03.json`. A conferência usou os resultados enviados na conversa, sem acesso direto ao Drive.

O diagnóstico de GPU `diagnostico_gpu_20261103T224137798314Z.json`, informado pelo pesquisador, aprovou a infraestrutura básica e identificou duas limitações do perfil BF16: falta de suporte nativo e 14,46 GiB de memória livre, abaixo dos 15,26 GiB estimados apenas para os pesos. O teste completo do E5 não foi executado.

## Decisão para o próximo teste

Foi preparado um perfil adicional de **QLoRA com NF4 em 4 bits e cálculo FP16**, identificado por `br_patstat_200_qwen3_8b_qlora_nf4_fp16_smoke_v1`. A base Qwen3-8B e sua revisão permanecem as mesmas. Quantização é uma alteração computacional relevante e deve constar na identificação de cada execução e em futuras comparações com o método publicado.

O perfil está em `config/perfil_qlora_teste.json`, separado da configuração que produziu os dados. O `experimento.json` continua com o mesmo hash para preservar a rastreabilidade dos resultados já conferidos. A configuração adicional é destinada a testar a viabilidade da alternativa na GPU disponível. Ela não declara treinamento completo ou qualidade experimental validada.

| Parâmetro | Teste de capacidade |
|---|---|
| Modelo | Qwen/Qwen3-8B, revisão congelada no projeto |
| Pesos quantizados | 4 bits NF4, com quantização dupla |
| Cálculo | FP16 nas operações configuradas; parâmetros LoRA treináveis em FP32 |
| LoRA | rank 8, alpha 16, dropout 0,05; q_proj e v_proj |
| Contexto do teste | Tensor de 2.048 tokens; padding mascarado quando necessário |
| Lote | Uma família por vez |
| Acumulação no teste | 1 |
| Atualizações do otimizador | 1 |
| Acumulação planejada para treino futuro | 16, a implementar após validar capacidade |
| Otimizador do teste | AdamW somente nos parâmetros LoRA, taxa 0,0003, weight decay 0,01 |
| Resultado | Relatório de diagnóstico; nenhum adaptador do teste é salvo para avaliação |

Os pesos de origem são baixados antes da quantização durante o carregamento. Portanto, 4 bits na GPU não significa um download de 4 GB nem garante que todo o consumo de memória se limite aos pesos quantizados. Embeddings, camadas não quantizadas, ativações, logits e otimizador também ocupam memória.

## Execução no Colab

1. Atualize a pasta do Drive com os arquivos da pasta local, incluindo `config/perfil_qlora_teste.json`, `scripts/testar_qlora_gpu.py`, o notebook 04 e `SHA256SUMS.txt` da mesma entrega.
2. Abra `04_testar_qlora_gpu.ipynb` com GPU. O diagnóstico 01 já realizado e os resultados 02/03 permanecem válidos para esta preparação.
3. Execute as células. A instalação respeita as versões nativas de PyTorch e NumPy. O teste roda em processo separado, com cache dos pesos em `/content`, fora do Drive.
4. Aguarde o download, carregamento e um passo de treinamento de diagnóstico. As mensagens mostram a fase em andamento.
5. Guarde e compartilhe o resumo final e o caminho do relatório. Ele é salvo no Drive em `resultados/etapa_1/piloto_br_200/qlora_teste_<UTC>.json`.

O script verifica os hashes da configuração, do relatório de pré-processamento e do arquivo de treino. Faz a medição dos comprimentos e recorta somente o resumo quando necessário, preservando título, instruções e resposta CPC. Registra o texto usado e a extensão do recorte. O CPC é o alvo supervisionado, sem inclusão no prompt de entrada.

A verificação de capacidade escolhe deterministicamente um dos registros mais longos do treino. Os exemplos de validação e teste não são usados para ajustar pesos. O padding até o limite é mascarado e não é tratado como texto da patente ou alvo de aprendizagem. Os valores do teste servem para verificar execução numérica, não para medir qualidade ou escolher o melhor adaptador.

## Interpretação do resultado

Um teste aprovado exige carga em GPU, perda e gradientes finitos, gradiente LoRA não nulo e alteração efetiva dos pesos treináveis após o passo de otimização. O relatório registra as versões e o consumo de memória observado. Falta de memória, erro de download ou atualização não realizada devem aparecer como falhas, com a fase correspondente.

Um passo bem-sucedido demonstra viabilidade inicial nessa sessão. Ainda será necessário implementar e validar o treinamento completo, a seleção do adaptador pela validação, a extração, o E5 e o alinhamento. O alvo CPC permanece esparso: 17 dos 20 rótulos de validação e 17 dos 20 de teste não aparecem no treino. Isso deverá ser considerado no plano de avaliação antes de interpretar desempenho.

O notebook e o script foram preparados para execução pelo pesquisador no Colab. A entrega local não executa o modelo de 8 bilhões de parâmetros e não confirma antecipadamente que ele caberá na GPU.

## Referências técnicas

- [PEFT — quantização e preparação para LoRA](https://huggingface.co/docs/peft/v0.18.0/en/developer_guides/quantization).
- [Transformers — bitsandbytes e NF4](https://huggingface.co/docs/transformers/v4.57.1/quantization/bitsandbytes).
- [Qwen3-8B — instruções oficiais do modelo](https://huggingface.co/Qwen/Qwen3-8B).
- [PyTorch — precisão mista e GradScaler](https://docs.pytorch.org/docs/2.9/notes/amp_examples.html).

As páginas versionadas documentam a série de APIs usada. As versões exatas de pacotes da execução continuam fixadas em `requirements.txt` e são registradas no relatório.

## Validação local antes da entrega

O tokenizador real da revisão fixada foi carregado em CPU, sem baixar pesos do modelo. Os 160 exemplos de treino ocuparam entre 208 e 744 tokens com o prompt e a resposta CPC, sem necessidade de recorte. A máscara foi conferida em todos eles: supervisão apenas sobre CPC e token de fim, com instruções, título, resumo e padding excluídos da perda. Um caso artificial longo testou o recorte do resumo, sem entrar na amostra empírica.

Nove testes de software passaram, incluindo integridade dos arquivos, bloqueio de registros de validação na entrada de treino, máscara de resposta, padding, fronteira de tokenização, excesso de contexto e relatório de falha sem biblioteca GPU disponível. As células do notebook foram compiladas e o fluxo de preparação foi exercitado com processos simulados. Esses testes não executam CUDA, não medem VRAM real e não substituem a execução do notebook04 no Colab.

O resultado da checagem real do tokenizador está em `resultados/etapa_1/piloto_br_200/validacao_tokenizador_qlora_cpu.json`.
