# Diagnóstico assistido — não é referência humana

Data: 08/11/2026. Produzido pelo assistente após observar os resultados; sem cegamento e sem adjudicação humana. Não enviar antes da anotação a um avaliador independente. As observações são hipóteses de erro para revisão, não rótulos de referência consolidados.

## Integridade e funcionamento

Hashes dos arquivos recebidos, script e perfil conferidos; as sete gerações foram revalidadas com o validador original. Agregados e métricas reproduzidos. Duração de 15,2 minutos, sem falta de memória. Base: elementos válidos em 1/2 e fluxo válido em 0/2. Adaptado: elementos e fluxo válidos em 2/2. A falha de elementos da base na família 50390156 (1.024 tokens, JSON incompleto) bloqueou relações. Na 68698300 a base produziu par com meme_1 repetido. Essas falhas não se convertem em listas vazias.

## Achados semânticos preliminares nas saídas adaptadas

| Família | Saída | Problema a revisar |
|---|---|---|
| 68698300 | “doenças” como material | O papel no texto é condição-alvo; não substância/material. |
| 68698300 | “divulgação” como processo | O termo designa o documento/ato de divulgar; não operação técnica descrita. |
| 68698300 | “Aumento da eficiência no tratamento de doenças” | “Eficazmente útil” não demonstra aumento de eficiência; verificar alegação e categoria separadamente. |
| 50390156 | “Redução de custos com a utilização de substrato sólido otimizado” | Nenhum custo ou economia está explicitado no título/resumo disponível. |
| 50390156 | “Ganho de eficiência na promoção de crescimento celular ou de tecido” | Otimização/finalidade no título não basta para afirmar ganho de eficiência. |

Pares de convergência também requerem inspeção: citar um trecho real ou unir componentes mencionados não comprova integração técnica. Não fizemos uma anotação exaustiva nem calculamos precisão, revocação ou F1. Não concluir superioridade do adaptador por dois JSONs válidos.

O ambiente reporta PyTorch 2.14.1+cu130. Comparações com 08/08b envolvem mudanças de protocolo, amostra, orçamento e ambiente; não atribuir diferenças de tempo/qualidade isoladamente ao LoRA. A comparação dentro de 08c compartilha ambiente mas tem apenas duas famílias de desenvolvimento.

Próxima decisão depende da revisão humana: identificar erros de definição, omissões e inferências sem suporte; só então especificar nova versão se justificada. Preservar tentativas inválidas e resultados antigos.
