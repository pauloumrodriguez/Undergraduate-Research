# Verificação local da entrega 08d

15/11/2026. Verificação em CPU; não mede qualidade semântica nem execução NF4 do modelo completo na GPU.

- Os 84 arquivos do índice anterior conferem com os hashes instalados. A árvore de QA contém cópias desses arquivos e os novos artefatos, sem referência anotada ou checkpoint de GPU. O preflight sem checkpoint seleciona exatamente 68698300 e 50390156.
- Modelo/checkpoint, seleção, estrutura, geração, dependências e semente devem permanecer iguais ao 08c. Mudanças de amostra, precisão ou orçamento foram rejeitadas. Alterar um prompt sem atualizar seu contrato foi rejeitado.
- Tokenizador real da revisão Qwen3-8B, em cache local e sem rede: sete cenários, de 1.188 a 2.581 tokens de entrada. Incluem elementos das duas famílias, relações com controle vazio e os três conjuntos válidos de elementos produzidos no 08c. Nenhum recorte. Os elementos novos do 08d podem ter comprimentos diferentes e serão conferidos em execução.
- Cobertura literal integral dos textos; schemas e gramática congelados; objetos vazios usados somente como controles sintéticos estruturais, não como respostas do experimento. Resposta sem EOS rejeitada. Entrada excessiva interrompe sem cortar o texto.
- Conferido que o payload contém somente trechos e, nas relações, elementos da própria variante. Não há leitura de referência anotada, contagens esperadas ou exemplos resolvidos. Ausência de gabarito não elimina a exposição prévia usada para desenvolver as regras.
- Código de todas as células compilado, sem saídas antigas ou execução residual.
- Teste integrado com GPU/modelo simulados: interrupção após duas respostas persistidas; retomada reutilizou as duas; sete chamadas concluídas quando uma falha de elementos bloqueou relações. Nenhuma resposta concluída foi regenerada, inclusive a inválida. Formulário de revisão preservado. Nova execução concluída não gerou mais chamadas. Ambiente divergente e conteúdo salvo adulterado foram rejeitados.

O núcleo real de geração/alternância de adaptadores é o mesmo extrair_evidencias_v3.py, conferido por hash e não modificado. Não repetimos testes caros de geração já aplicados a esse núcleo. Não foi baixado nem executado o modelo completo localmente. O teste real do 08d na GPU e sua comparação semântica com 08c continuam pendentes.

Evidência estruturada: resultados/etapa_5d/piloto_br_200/validacao_local_08d.json. A entrega exige o checkpoint e dados existentes no Drive; eles não estão no ZIP de atualização.
