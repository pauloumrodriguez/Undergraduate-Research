# Referência de desenvolvimento v3 — seis famílias de validação

Consolidada em 19/11/2026, antes de qualquer previsão do 08d nas quatro famílias novas. Não houve nova geração nem treinamento.

## Composição

| Famílias | Origem | Situação |
|---|---|---|
| 68698300, 50390156 | Referência v2 (08c), copiada sem alteração | Anotada após ver previsões; edição assistida por IA conforme D1–D5; usadas para formular as regras |
| 45975308, 65439381, 74045448, 80949080 | Revisão `revisao_humana_validacao4` (JSON exportado em 19/11/2026T18:14Z) | Anotação humana direta sob D1–D5; sem previsões na ficha; exposição prévia autodeclarada: não |

45 itens no total. Contagem por grupo em `referencia_consolidada.json → contagens_itens`. **Nenhum par de convergência** foi anotado nas seis famílias.

## Conferências feitas na consolidação

- Hashes de textos, entradas, perfil das seis famílias e regras D1–D5 do JSON coincidem com `proveniencia.json` da revisão.
- Toda evidência das quatro famílias novas é cópia literal do campo indicado, com posições Unicode coerentes e sem ocorrência ambígua; IDs relacionados existem; pares usariam dois memes distintos (não há pares).
- Nenhum grupo ficou indeterminado: 15 anotados e 9 ausentes com justificativa.
- Os textos das quatro famílias são idênticos aos de `entradas_extracao.jsonl`.

## Limites que devem acompanhar qualquer resultado

- Um único anotador; sem adjudicação; sem concordância entre avaliadores.
- As regras D1–D5 foram formuladas a partir das duas primeiras famílias. Nas quatro novas elas foram aplicadas por quem as conhecia.
- As quatro famílias já tiveram previsões em 08/08b; a ficha não as mostrou, mas isso não é amostra virgem.
- Sem pares positivos, a referência não avalia convergência, insumo central do EDh. Métricas de pares ficam indefinidas/vazias, não perfeitas.
- Itens ausentes na referência não provam que o modelo errou ao propor algo; metrica condicional à lista atual.
- Esta referência não deve ser editada para coincidir com a saída do 08d. Qualquer revisão terá versão separada e reavaliará 08c e 08d.

Congelada pelo hash registrado em `config/perfil_extracao_validacao4_v4.json`. O programa de extração não a lê.
