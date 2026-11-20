# Etapa 2 — treinamento exploratório CPC com QLoRA

Protocolo de execução registrado em 4 de novembro de 2026, antes do treinamento completo. Perfil: `config/perfil_treino_qlora_1024.json`. Este documento complementa `docs/ADAPTACAO_METODOLOGICA_BR.md`; não altera a seleção congelada nem os hashes do pré-processamento.

## Evidência de capacidade disponível

O pesquisador enviou o resumo do diagnóstico `qlora_teste_20261104T014632833741Z.json`: estado `teste_qlora_aprovado`, perfil `br_patstat_200_qwen3_8b_qlora_nf4_fp16_smoke_v2_ctx1024`, perda 5,8950114250183105, pico alocado 11,768 GiB, pico reservado 12,605 GiB, duração 861,432 segundos e nenhum erro. O JSON completo permanece no Drive e será conferido pelo notebook 05 antes do treinamento. Esse resumo é evidência comunicada pelo pesquisador; não equivale a uma nova execução GPU local.

O diagnóstico comprova um passo nesse ambiente. A perda isolada não mede acurácia, ganho sobre a base ou qualidade da extração. A duração inclui preparação/carregamento e não permite estimar diretamente três épocas. A estabilidade do treinamento completo ainda precisa ser observada.

## População, supervisão e separação

- 200 famílias DOCDB do pacote PATSTAT previamente extraído, com vínculo BR e depósitos de 2010–2024. O recorte disponível é CPC A61 ou C12N; as limitações do filtro IPC original e da origem dos textos constam na auditoria brasileira.
- Treino: 160 famílias. Validação: 20 famílias. O programa de treinamento não abre o arquivo das 20 famílias de teste.
- Entrada: título, resumo e idiomas pt/en. Sem tradução e sem rótulo CPC nas instruções ou nos textos de entrada.
- Alvo: `alvo_cpc_proxy`, o símbolo CPC integral herdado da seleção alfanumérica do pacote, seguido do marcador de fim da resposta. Não representa um código principal oficial ou uma anotação humana.
- O adaptador é treinado para esse alvo CPC. Ele não recebe supervisão dos seis campos da extração; esses campos exigirão avaliação própria e evidências textuais.

Há 142 rótulos CPC distintos nas 160 famílias de treino. Em 17 das 20 famílias de validação, o código integral não aparece no treino. Manter os códigos como congelados; qualquer futura avaliação por nível hierárquico precisa de definição explícita antes de inspecionar resultados de teste. Não escolher classes, épocas ou exemplos pelo teste.

## Parâmetros e justificativas

| Item | Escolha deste piloto | Justificativa |
|---|---|---|
| Modelo | Qwen/Qwen3-8B, revisão `b968826d9c46dd6066d109eabc6255188de91218` | Escala autorizada pelo pesquisador; revisão congelada |
| Base quantizada | NF4, double quant, cálculo FP16 | Perfil que completou o diagnóstico na GPU disponível |
| LoRA | rank 8, alpha 16, dropout 0,05, `q_proj` e `v_proj`, bias none | Continuidade com o diagnóstico; não é LoRA em todas as camadas lineares |
| Contexto | Até 1.024 tokens, uma sequência por microbatch, sem padding fixo | Preserva os exemplos auditados e reduz trabalho em posições vazias |
| Lote efetivo | 16 famílias, acumulação de 16 microbatches | Mantém lote efetivo planejado sem carregar 16 sequências simultaneamente |
| Treinamento | 3 épocas, 10 atualizações por época, 30 no total | Plano fixado antes de ver perdas de validação |
| Otimizador | AdamW, taxa 0,0003, weight decay 0,01, norma máxima 1 | Taxa/decay do plano; clipping para controle numérico |
| Agenda | Taxa constante, warmup zero | Escolha declarada porque o artigo não especifica o scheduler |
| Precisão | AMP FP16 e GradScaler, adaptadores treináveis FP32 | Consistência com a preparação PEFT e o diagnóstico |
| Memória | Gradient checkpointing, cache de atenção desativado | Continuidade com a configuração aprovada |
| Semente | 42; permutação determinística por época | Possibilita verificar ordenação e retomada |

O limite de contexto não trunca automaticamente o alvo. A função reutilizada preserva instruções, título e CPC, e registra eventual recorte do resumo. A conferência CPU com o tokenizador real mediu 208–744 tokens no treino e 181–699 na validação: nenhum recorte nos 180 exemplos. A normalização e a divisão de famílias permanecem congeladas.

## Perda, validação e escolha do adaptador

Os tokens de instruções, título e resumo recebem máscara `-100`; a perda é calculada somente nos tokens CPC+EOS. Para cada grupo efetivo de 16 famílias, a perda média de cada exemplo é multiplicada por sua contagem de tokens supervisionados e dividida pelo total do grupo. Isso corresponde à média global por token, sem uma segunda divisão por 16.

A validação usa a mesma média por token nas 20 famílias, sem gradientes, antes do treino (referência base) e ao final das três épocas. Entre os adaptadores das épocas 1, 2 e 3, selecionar aquele com menor perda de validação. Em empate, conservar a primeira época. A referência anterior ao treino é reportada separadamente, não candidata a adaptador treinado.

Se todas as épocas piorarem em relação à base, o melhor adaptador treinado ainda será identificado, mas a piora deverá ser explicitada. Não alegar benefício do ajuste apenas porque a execução terminou. Esta etapa não calcula acurácia por geração nem métricas de extração, alinhamento ou novidade tecnológica.

## Artefatos e retomada

O notebook chama o programa em um processo separado. Os pesos originais ficam no cache temporário do Colab; não são copiados integralmente para o Drive. Salvar adaptadores e tokenizador, perdas, ambiente, hashes, contagens de tokens e memória em `resultados/etapa_2/piloto_br_200/`.

Os checkpoints são gravados a cada cinco atualizações e nos finais de época, com adaptador, estado do otimizador, GradScaler, geradores aleatórios e posição de continuação. Um checkpoint só é considerado completo quando seu manifesto final existe e os hashes conferem. Arquivos parcialmente gravados após uma desconexão não devem ser usados.

Para retomar, usar o caminho de checkpoint indicado pelo relatório no campo `RETOMAR_CHECKPOINT` da célula inicial do notebook 05. É necessário manter perfil, arquivos, programa e versões compatíveis. A retomada parte do último checkpoint completo, podendo repetir o trabalho posterior a ele. Não editar hashes para aceitar uma incompatibilidade. O teste de CPU valida a lógica de persistência; a equivalência bit a bit entre GPUs/sessões distintas não é garantida.

## Execução pelo pesquisador

1. Atualizar no Drive o notebook 05, o novo programa, o perfil e o índice de arquivos. O notebook também exige a mesma versão de `scripts/testar_qlora_gpu.py` que foi usada no 04b; incluir esse arquivo na atualização.
2. Abrir `notebooks/05_treinar_qlora_cpc.ipynb` no Colab com GPU. Manter a raiz e o caminho do diagnóstico aprovado que já vêm preenchidos. Na primeira execução, deixar `RETOMAR_CHECKPOINT` vazio.
3. Executar as células em ordem. O notebook verifica arquivos e relatório, instala dependências preservando PyTorch/NumPy da sessão, e inicia o treinamento. Seguir uma eventual instrução explícita de reinício da célula de instalação.
4. Acompanhar as atualizações e os checkpoints no Drive. O plano inclui 480 microbatches de treino e 80 passagens de validação ao longo das três épocas e da referência inicial; não são apenas 30 passagens pelo modelo.
5. Ao terminar, enviar o resumo final com estado, perdas de referência e validação, época selecionada, atualizações concluídas, memória e caminhos do adaptador/relatório. Em falha, enviar o erro e o último checkpoint completo.

Não é necessário repetir 00, 02, 03, 01 ou 04b apenas para iniciar o 05 após a conferência dos arquivos. GPU nova ou diferente ainda pode ter comportamento de memória distinto. Não executar E5 simultaneamente com o treinamento Qwen. A conclusão do 05 permite preparar a comparação de extração base versus adaptador e o alinhamento; não conclui a replicação inteira.

## Referências de implementação

- [PEFT 0.18 — treinamento com quantização](https://huggingface.co/docs/peft/v0.18.0/en/developer_guides/quantization): preparação k-bit e adição de LoRA sobre base quantizada. Módulos q/v são a escolha limitada deste piloto.
- [PyTorch — exemplos AMP](https://docs.pytorch.org/docs/2.9/notes/amp_examples.html): manter a escala durante acumulação, remover a escala uma vez por atualização e aplicar clipping depois disso.
