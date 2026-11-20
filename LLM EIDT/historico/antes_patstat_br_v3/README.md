# LLM-EIDT · Piloto de 200 patentes com Qwen3-8B

**Etapa 1 · Protocolo, acesso e ambiente · 02/11/2026**

Este projeto prepara uma reconstrução independente do estudo de Ding e Lu com uma coleta nova de patentes chinesas de ciências da vida. A unidade do piloto é **uma publicação representativa por família**. O modelo escolhido para a adaptação CPC por LoRA e a extração é o **Qwen/Qwen3-8B**. Os primeiros resultados que interessam são cobertura dos dados, execução na GPU disponível, qualidade da extração e custo por patente. O preprint usou Qwen3-14B, 14.265 patentes e amostras próprias. Os números publicados estão preservados como referência em `publicado` e o protocolo desta experiência está em `piloto`. [Configuração](config/experimento.json) · [Artigo v1](https://doi.org/10.21203/rs.3.rs-9585548/v1)

## 1. Executar no Colab

No Windows, a raiz é `C:\Users\paulo\Desktop\Replicação LLM EIDT IC`. Em **Meu Drive**, envie ou sincronize a versão atualizada da pasta. Se já tiver executado a versão de 14B, mantenha os relatórios anteriores e atualize o conteúdo da mesma pasta, verificando que o Drive não criou arquivos duplicados com o mesmo nome. O arquivo `config/experimento.json` deve mostrar `Qwen/Qwen3-8B` em `modelos.qwen.id`. Confirme que o novo índice `SHA256SUMS.txt` e a pasta `scripts` estão na raiz que contém `requirements.txt`. O caminho padrão de todos os notebooks é `/content/drive/MyDrive/Replicação LLM EIDT IC`.

| Ordem | Ambiente | O que fazer e conferir |
|---|---|---|
| [00 · Preparar o Drive e auditar insumos](notebooks/00_preparar_drive_e_auditar_insumos.ipynb) | CPU | Abra com o Google Colaboratory, monte o Drive e execute em ordem. Confira as revisões dos dois modelos e a integridade da cópia. O inventário deste piloto começa pelo PDF e registra as pendências de coleta e anotação. O notebook usa `config/insumos_piloto_200.csv`. |
| [01 · Validar GPU e modelos](notebooks/01_validar_gpu_e_modelos.ipynb) | GPU | Em **Ambiente de execução → Alterar o tipo de ambiente de execução**, selecione GPU e, se disponível, a versão **2026.01**. Execute em ordem. Se a instalação alterar pacotes, selecione **Reiniciar sessão** e execute tudo de novo na mesma máquina virtual. Na primeira passagem, mantenha desligados os testes opcionais com pesos reais. O teste padrão confere o perfil de extração e tokeniza uma entrada chinesa curta. Confira o estado do diagnóstico, o nome da GPU e o campo `perfil_lora_8b`. |
| [02 · Registrar a coleta e selecionar as 200](notebooks/02_registrar_coleta_e_selecionar_200.ipynb) | CPU | Execute após obter a exportação nova. Preencha a declaração de origem na primeira vez, confira a cobertura por janela, o isolamento por família e os rótulos CPC. Na ausência do CSV, o notebook aponta a pendência. A seleção e o diagnóstico de GPU são independentes. |

O ambiente de referência usa Python 3.12, a pilha CUDA/PyTorch do Colab e dez dependências com versão fixada. Entre elas estão Transformers, PEFT, Accelerate e bitsandbytes. O script de seleção usa somente a biblioteca padrão do Python 3.11 ou posterior. Confira os relatórios persistidos no Drive e traga-os ao Desktop ao terminar. [Dependências](requirements.txt) · [Versões do ambiente Colab](https://research.google.com/colaboratory/runtime-version-faq.html)

## 2. Coleta nova

1. Acesse o AI Pat+ por uma conta ou instituição com permissão para exportar. Confirme a disponibilidade dos campos e se a exportação pode ser armazenada no Drive. Registre separadamente restrições de cobertura, paginação, ordenação e exportação. [AI Pat+](https://aipat.cnki.net/)
2. Refaça a consulta de ciências da vida usando o escopo da § 4.1. Abrange China, língua chinesa, pedidos e concessões de invenção, “Life Sciences” em palavras-chave, título DWPI ou resumo DWPI, fusão de famílias e **depósitos de 01/01/2000 a 30/06/2025**. Guarde a expressão efetivamente aceita, as opções da interface e a data real da exportação. O número de resultados de uma busca nova pode divergir daquele da v1.
3. Exporte um universo com famílias suficientes nas três janelas. Salve o CSV UTF-8 em `dados/brutos/piloto_200/exportacao.csv`. Se converter uma planilha exportada, preserve o arquivo original, os identificadores como texto e a descrição da conversão. O CSV aceita vírgula, ponto e vírgula ou tabulação. O piloto usa a totalidade dos candidatos elegíveis fornecidos ao seletor. Uma exportação parcial limita a população à qual o sorteio se aplica.
4. Confira os campos abaixo e preencha, se necessário, o dicionário `MAPA` no 02. A declaração de nova coleta produz `dados/brutos/piloto_200/proveniencia.json`, com o SHA-256 do CSV. Este registro permite verificar depois quais bytes entraram no sorteio. Cabe ao pesquisador confirmar a consulta, a origem, a língua e o escopo real.

| Campos canônicos | Verificação |
|---|---|
| `id_publicacao`, `id_familia` | IDs estáveis da fonte, sem conversão numérica nem remoção de zeros. A família deve identificar publicações relacionadas entre as três janelas. |
| `data_deposito`, `data_publicacao` | Preferir ano-mês-dia. Usar as datas da publicação representativa e conferir a ordem cronológica. |
| `titulo_zh`, `resumo_zh` | Texto original em chinês. O seletor verifica presença de ideogramas nos dois campos como controle básico. |
| `cpc_principal` | Categoria principal identificada pela fonte. Um campo vazio pode participar da amostra textual. Para autorizar o desenho CPC de 160/20/20, verificar cobertura completa, nível e origem dos rótulos. O código não infere o alvo pelo título. |

## 3. Congelar a amostra

O [seletor](scripts/selecionar_piloto.py) usa o ano de depósito para alocar a janela. Entre as publicações elegíveis da mesma família nas três janelas, escolhe a de menor data de depósito, depois a de menor data de publicação e, persistindo o empate, o menor ID de publicação. Em cada janela, ordena famílias com SHA-256 e semente 42. Usa uma segunda ordenação determinística para atribuir partições. Isso permite repetir a seleção mesmo se mudar a ordem das linhas da exportação.

| Janela de depósito | Treino | Validação | Teste | Total |
|---|---:|---:|---:|---:|
| 2010–2014 | 54 | 7 | 6 | 67 |
| 2015–2019 | 53 | 7 | 7 | 67 |
| 2020–2024 | 53 | 6 | 7 | 66 |
| **Total de famílias** | **160** | **20** | **20** | **200** |

As cotas dão peso semelhante a cada período para exercitar o fluxo. Após o sorteio, abra `dados/processados/piloto_200/auditoria.json` e confira quantidades, exclusões, cobertura CPC e os hashes. O arquivo `piloto_200.csv` preserva o ID de família e a partição de cada patente. A falta de candidatos em uma janela interrompe a seleção. Se precisar ampliar a busca, arquive o CSV e o recibo da tentativa anterior juntos e registre a nova exportação. Se já houver uma amostra congelada, faça a nova execução em uma cópia versionada do projeto. Uma repetição com os mesmos dados e configuração preserva a amostra.

## 4. Perfil de ML adotado

| Decisão do piloto | Parâmetros e motivo |
|---|---|
| **Modelo e precisão** | Qwen3-8B com revisão imutável, base BF16 congelada e LoRA em GPU com suporte nativo a BF16. Os pesos somam aproximadamente **15,26 GiB**. Ativações, gradientes dos adaptadores e memória de trabalho elevam o consumo. O diagnóstico compara o piso com a VRAM livre. |
| **Ajuste CPC** | Uma GPU, microlote **1**, acumulação de **16**, lote efetivo **16**, até **2.048 tokens**, recomputação de ativações e cache de geração desativado no treino. Medir o percentual de títulos/resumos recortados antes de congelar esse comprimento. A entrada usa título e resumo. O CPC principal é o alvo. |
| **Adaptadores** | LoRA em `q_proj` e `v_proj`, posto **8**, `alpha=16`, `dropout=0,05`. Isso limita os pesos treináveis. Preservamos do artigo a taxa de **0,0003**, o decaimento **0,01** e **3 épocas**. Com as 160 famílias rotuladas, o plano dá **10 atualizações por época**. Avaliar por época permite observar a validação durante as 30 atualizações previstas. |
| **Extração** | Usar o mesmo Qwen3-8B com o adaptador CPC escolhido na validação. Uma patente por vez, geração gulosa, `enable_thinking=False`, até **2.048 tokens de entrada e 1.024 novos tokens**. Registrar truncamentos, preservar a saída bruta e validar os seis campos em JSON e os trechos de evidência. |
| **Embeddings e capacidade** | Mantemos o multilingual-e5-large. Execute E5 e Qwen em momentos separados para liberar memória. O 01 oferece dois testes opcionais com pesos reais. O E5 baixa cerca de 2,24 GB. O Qwen baixa cerca de 16,4 GB e exercita uma passagem sintética de ajuste em BF16. Ative esse teste apenas na GPU que pretende usar. O resultado de um microlote distingue falha de memória de viabilidade preliminar. QLoRA/NF4 requer um perfil separado, identificado nos resultados. |

O modelo de origem e os módulos LoRA vêm de referências distintas. O repositório oficial fixa a arquitetura carregada. As escolhas de tamanho de sequência, módulos e precisão acima pertencem ao piloto. [Revisão do Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B/tree/b968826d9c46dd6066d109eabc6255188de91218) · [Revisão do E5](https://huggingface.co/intfloat/multilingual-e5-large/tree/ab10c1a7f42e74530fe7ae5be82e6d4f11a719eb)

## 5. Validações e critérios de saída

- **Ambiente pronto para o piloto.** O 00 confirma o PDF e a nova configuração. O 01 grava a GPU, VRAM, versões, revisões, operações LoRA e o estado dos testes opcionais. Compare a VRAM livre com o piso BF16. Se for insuficiente, reserve outra GPU para o treino de referência ou documente uma futura execução QLoRA com configuração própria.
- **Amostra pronta para extração.** A exportação tem origem registrada, a auditoria confirma 200 famílias distintas e as partições batem com a tabela. Para treino CPC, valide ainda a cobertura de rótulos nas três partições. Trate eventuais rótulos ausentes antes de aprovar um experimento supervisionado com o tamanho declarado.
- **Qualidade do extrator.** Na etapa de avaliação, prepare anotações humanas independentes para as famílias de teste e fixe as regras de correspondência antes de examinar previsões. Compare o Qwen3-8B sem adaptador e com LoRA nos mesmos documentos e condições. Relate precisão, revocação e F1 por campo, taxa de JSON válido, suporte textual, truncamentos, memória de pico e tempo por patente. O teste reservado tem 20 famílias. Divulgue contagens junto às métricas. Uma conclusão sobre equivalência ao 14B dependeria de comparação controlada dos dois tamanhos.
- **Validade histórica.** As primeiras ocorrências nas 200 famílias são relativas à amostra. Uma avaliação do EDh e do Dh requer histórico anterior suficiente, temas comparáveis e grafo datado de citações. A configuração preserva as duas leituras da Tabela 7 e o teste da ablação de convergência para quando essa análise for possível.

Ao fim da Etapa 1, guarde o inventário e o último diagnóstico da GPU. Quando houver coleta, acrescente o recibo, a auditoria da seleção e o comprovante em `resultados/etapa_1/piloto_200/`. O estado inicial da entrega contém o PDF e a infraestrutura do piloto. Os dados empíricos começam com a sua nova exportação.
