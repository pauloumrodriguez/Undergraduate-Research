# Revisão das quatro famílias restantes — regras D1–D5

## O que fazer agora

1. Abra ABRIR_REVISAO.html no Chrome ou Edge. Não é notebook: não precisa de Colab, GPU, conta Google ou instalação. Se estiver no ZIP, extraia antes.
2. Preencha seu nome e a exposição a previsões/comentários destas quatro famílias, inclusive dos notebooks 08/08b. Se não lembrar, marque “Não tenho certeza”. Se viu só algumas, identifique-as nas observações. Conhecer as regras e os dois casos anteriores não equivale a ter visto as previsões destas quatro famílias.
3. Leia título e resumo de cada família. Preencha os seis grupos com as regras D1–D5 mostradas na própria ficha. A ficha começa vazia e contém somente as fontes e orientações, sem candidatos do modelo.
4. Copie evidências literalmente do campo correto. Preserve acentos, caixa e espaços. Amplie o trecho se houver mais de uma ocorrência no mesmo campo. Pode citar título e resumo para um item, mas não fundir alegações incompatíveis. O programa calcula posições Unicode; existência de citação não comprova sua interpretação.
5. Nos pares, use dois IDs distintos de memes que você anotou; nos efeitos, use IDs de elementos somente quando o vínculo estiver sustentado. A lista de vínculos pode ficar vazia. Não use IDs de efeito/par para vínculos de efeitos.
6. Use “Ausência de evidência após revisão” somente após ler o grupo. Quando a interpretação não estiver resolvida, marque “Indeterminado” e explique. Não force uma resposta para concluir. Grupos não revisados continuam pendentes.
7. Clique em Baixar rascunho ao terminar cada família. NÃO há salvamento automático. Para continuar, importe o JSON salvo em “Continuar um JSON salvo desta ficha”. A nova ficha rejeita os JSONs do 08c, pois contêm outras famílias/versão.
8. Ao terminar as quatro famílias, clique em Concluir e baixar revisão. Envie aqui o arquivo revisao_humana_validacao4_preenchida_…json. Indeterminações podem ser exportadas, mas permanecem pendentes de adjudicação. Guarde também uma cópia no Drive em Replicação LLM EIDT IC/revisao_humana_validacao4.

## Critérios consolidados

- **Memes:** unidade técnica contextualizada e central. Excluir rótulos genéricos isolados, propriedades físico-químicas como memes autônomos e métodos empregados só para caracterização/controle. Não transformar todo substantivo do texto em tecnologia.
- **Funções:** finalidade ou ação explícita com alvo, negação e modalidade. Manter alternativas conjuntas em uma unidade, incluindo os operadores ou/e/e-ou conforme o original. Não concluir ação causal a partir de associação. Finalidades diferentes de título/resumo permanecem separadas.
- **Materiais:** entidades distintas em itens distintos; separar formulação, substância, forma alternativa e material-base/suporte quando expressos. Relação parte–todo não torna entidades equivalentes. Separar alternativas não afirma coexistência.
- **Processos:** operações explicitamente nomeadas ou descritas, sem exigir etapas detalhadas. Separar operações distintas; manter alternativas da mesma operação unidas. Medição pode constituir processo sem tornar método auxiliar um meme central. Não inventar procedimentos para produzir um material.
- **Convergência:** integração técnica sustentada entre dois memes centrais distintos. Coocorrência, enumeração, parte–todo, alternativa, representação, objeto/propriedade, objeto/operação ou medição não bastam isoladamente. Não preencher pares por obrigação.
- **Efeitos:** resultado alcançado explicitamente alegado, preservado como alegação, não comprovação experimental. Finalidade não é duplicada automaticamente como efeito. Custo e eficiência exigem suporte explícito específico. Usar outro apenas para outro resultado alegado com suporte.

Não há quantidade esperada de itens por família/grupo. Listas vazias revisadas são diferentes de falhas e de indeterminação. Os textos podem não fornecer detalhes suficientes: registrar a limitação é preferível a completar com conhecimento externo. Não traduzir citações nem corrigir o texto de origem; títulos/resumos preservam a cópia congelada do pré-processamento.

## Seleção e alcance

Famílias 45975308, 65439381, 74045448 e 80949080. São exatamente as quatro restantes do piloto de seis famílias de validação dos notebooks 08/08b, após retirar 50390156 e 68698300 já revisadas. Não houve seleção por acerto, troca de amostra, acesso ao conjunto de teste ou nova geração. Os hashes e a regra constam em proveniencia.json.

Todas têm título/resumo marcados como português nos metadados. Não foi feita nova detecção automática de idioma. Origem por aplicação de cada campo continua desconhecida: diferenças não provam que os textos sejam de documentos distintos. A amostra é parte de uma adaptação PATSTAT Brasil, não o corpus chinês original.

Essas famílias já tiveram previsões em 08/08b. A ficha não as inclui, mas não apaga exposições passadas; esta não é amostra de teste virgem. As regras foram desenvolvidas após observar outras duas famílias. Registre ajuda de outras pessoas/IA e consultas. Um segundo anotador pode usar uma cópia separada, sem ver sua ficha; não misturar anotações antes de preservá-las. Não afirmar concordância entre avaliadores quando há só um.

## Depois da revisão

Conferir preenchimento/evidências, resolver indeterminações e congelar a referência antes de olhar novas previsões. Em seguida preparar a execução das quatro famílias com as instruções 08d já fixadas, sem nova rodada de ajustes por resultado favorável. O notebook 08d atual seleciona apenas as duas famílias antigas: não o rode para tentar avaliar estas quatro.

Este pacote contém apenas a ficha, fontes e regras. Não treina modelo, não executa extração, não calcula métricas e não inclui novo notebook. Não precisa atualizar SHA256SUMS.txt do projeto: MANIFESTO_SHA256.txt confere esta entrega separada.

## Arquivos

- ABRIR_REVISAO.html: arquivo principal, autossuficiente e sem rede. Basta abrir localmente.
- LEIA_PRIMEIRO.md: este guia.
- REGRAS_D1_D5.md: cópia exata do registro geral de regras do projeto.
- textos_originais.json e proveniencia.json: fontes e rastreabilidade, sem previsões.
- MANIFESTO_SHA256.txt: integridade da entrega.

Para backup, pode enviar revisao_humana_validacao4.zip à pasta entregas do Drive, sem extrair ali. Para preencher, use a ficha local; para guardar o trabalho feito, envie o JSON que você exportar, não apenas o ZIP vazio de anotações.
