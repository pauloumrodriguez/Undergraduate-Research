# Verificação local da entrega 08d-validacao4

19/11/2026. Verificação em CPU; não mede qualidade semântica nem execução NF4 do modelo na GPU.

- Preflight sem checkpoint seleciona exatamente 45975308, 65439381, 74045448 e 80949080, nessa ordem; os textos coincidem com `entradas_extracao.jsonl` e com `revisao_humana_validacao4/textos_originais.json`. Idiomas pt/pt; 6, 5, 3 e 4 trechos de até 256 caracteres, cobertura literal integral.
- Rejeitados em teste: trocar a amostra, aumentar o orçamento (32), alterar a geração, alterar hash de prompt, trocar o arquivo de prompt, marcar referência usada na geração e alterar o checkpoint. O perfil original é aceito.
- Diferença entre a função `run` do 08d e a do 08d-validacao4 conferida linha a linha: apenas número de famílias (4), orçamento (16), verificação final (8 fluxos), rótulos de estado e pasta de resultados.
- Prompts, regras, schemas, gramática, dependências, núcleo 08c e script 08d: iguais por hash aos do 08d.
- Não medido: tokens de entrada com tokenizador real (ambiente local sem `transformers`); a maior família nova tem 1.313 caracteres contra 1.984 da maior do 08d (2.581 tokens). Entrada excessiva interrompe sem recorte. Também não rodado: GPU, modelo e retomada simulada; o código de geração/persistência é o do 08d, sem alteração.
- A referência v3 não é aberta pelo programa; só o notebook confere seu hash de integridade.

O teste real e a qualidade da extração serão medidos no Colab.
