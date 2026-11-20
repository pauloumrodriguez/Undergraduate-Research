# Referência consolidada e comparação 08c

**D1–D5 registradas e aplicadas.** Anotação original preservada; nova versão tem 14 itens, antes 9. Não houve GPU, novo treino ou alteração de notebooks.

## Alterações efetivas

- Família 68698300: três materiais distintos (composição, composto e sal), finalidade conjunta preservada e alegação terapêutica mantida como efeito “outro”.
- Família 50390156: substrato e derivado separados; quatro processos (seleção, determinação da absorção, medição da rugosidade e conversão); finalidade de crescimento removida de efeitos; fonte desconhecida e citação com e/ou registradas.
- Memes humanos existentes preservados, sem adicionar automaticamente novos candidatos centrais. Propriedades e microscopias auxiliares excluídas do papel de memes conforme D1.

## Comparação descritiva condicional

A tabela avalia os fluxos completos contra esta referência. A base continua com 0/2 fluxos válidos; o adaptado com 2/2. Itens da base em etapas isoladas não são resgatados. Falhas não são declaradas ausência de informação.

| Grupo | Referência | TP adaptado | Sem correspondência (FP) | Não recuperados (FN) |
|---|---:|---:|---:|---:|
| memes_tecnicos | 1 | 1 | 11 | 0 |
| funcoes | 3 | 0 | 6 | 3 |
| materiais | 5 | 1 | 1 | 4 |
| processos | 4 | 3 | 1 | 1 |
| pares_convergencia | 0 | 0 | 12 | 0 |
| efeitos | 1 | 0 | 4 | 1 |

As cinco correspondências do adaptado são: derivado marinho como meme; derivado marinho como material (papel distinto); seleção, determinação de absorção e medição de rugosidade como processos. Não são cinco famílias ou cinco tecnologias independentes.

| Variante | TP | FP | FN | Precisão | Revocação | F1 condicional |
|---|---:|---:|---:|---:|---:|---:|
| base | 0 | 0 | 14 | — | 0.0% | 0.0% |
| adaptado | 5 | 35 | 9 | 12.5% | 35.7% | 18.5% |

**Estes números não são avaliação independente nem F1 definitivo.** São cálculos condicionais a uma referência de desenvolvimento revista após exposição. O assistente aplicou as correspondências; não houve segunda adjudicação humana. Duas saídas de memes centrais ainda têm ressalva de cobertura da referência. “FP” designa falta de correspondência nesta lista/regra, não necessariamente afirmação inventada.

A regra de modalidades unidas impede contar prevenção e tratamento separados como recuperação integral do item conjunto. A função com “e” não equivale à referência “e/ou”. O efeito que cobre só tratamento, com vínculos inadequados, não corresponde ao objeto humano completo. Essas escolhas estritas estão explícitas no protocolo e no JSON por item.

## Próximo passo

Preparar um protocolo de geração 08d incorporando D1–D5, sem modificar 08c, e testá-lo antes de entrega. Ainda não existe notebook 08d pronto neste pacote. Não repetir os notebooks atuais esperando que usem as novas regras. A referência está consolidada para desenvolvimento; a cobertura e a generalização exigem avaliação em outras famílias, sem usar o teste para escolher regras.

## Arquivos

referencia_consolidada.json pode ser consultado diretamente ou importado na ficha original para leitura/edição. Se reexportar pela ficha, preserve este arquivo, pois o exportador usa seus estados próprios. decisoes_humanas_D1_D5.json preserva as decisões recebidas. alteracoes_referencia.json lista cada alteração. comparacao_e_metricas_condicionais.json contém o mapeamento completo e os limites. originais/ preserva a anotação recebida e as fontes. MANIFESTO_SHA256.txt confere esta entrega sem substituir o índice do projeto.
