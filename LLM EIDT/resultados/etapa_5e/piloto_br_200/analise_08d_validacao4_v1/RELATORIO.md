# 08d em quatro famílias novas de validação — comparação com a referência v3

19/11/2026 · análise assistida por IA (mapeamento um a um feito pelo assistente, sem adjudicação humana) · desenvolvimento, não teste independente.

## Conclusão

O 08d com as instruções D1–D5 congeladas **completou 6 de 8 fluxos**, mas a qualidade nas famílias novas é baixa: o melhor caso (adaptado, leitura branda) tem F1 condicional de 37,5%, e a precisão nunca passa de ~31%. Nada aqui autoriza escolher base × adaptado, estender às 200 famílias ou seguir ao alinhamento.

Nestas quatro famílias o adaptado ficou **à frente da base** (o oposto das duas famílias de desenvolvimento). Com 4 famílias, uma referência de um anotador e duas falhas estruturais pesando muito, isso é compatível com ruído, não evidência de ganho do LoRA CPC.

## Integridade e execução

SHA-256: extracoes.jsonl `e8f08a96f3302441…`, geracoes.jsonl `170714a355a076e0…`, referência v3 `3fea669a357dd25d…` (igual ao registrado no perfil antes da execução). Execução limpa (0 retomadas), T4, 1.135 s, pico reservado 12,56 de 14,56 GiB. Chamadas: 14 de 16 (as 2 de relações bloqueadas não existem).

| Família | Variante | Elementos | Relações | Observação |
|---|---|---|---|---|
| 45975308 | base e adaptado | inválido | bloqueado | 1.024 tokens atingidos, sem EOS, JSON cortado no meio de uma string; 27 termos já enumerados (inclui pedaços como "monômero") |
| 65439381 | base e adaptado | válido | válido | — |
| 74045448 | base e adaptado | válido | válido | — |
| 80949080 | base | válido, **todas as listas vazias** | inválido | `["indisponivel"]` em `relacionado_a` de dois efeitos |
| 80949080 | adaptado | válido | válido | — |

Fluxos completos válidos: adaptado 3/4, base 2/4. As falhas ficam no denominador (45975308 conta 9 itens de referência não recuperados em cada variante). Na base de 80949080, só elementos entram na conta; pares e efeitos rejeitados não contam como previsões.

## Métricas condicionais (31 itens de referência nas 4 famílias)

Regra: correspondência um a um, no mesmo grupo, por conceito/papel/contexto; operadores e alternativas preservados; menção em outro grupo não recupera item. Há dois cenários porque muitos itens são **parciais** (mesmo conceito, mas sem o qualificador, o alvo ou o objeto da referência, por exemplo "tratar dor ou irritação" sem "em uma articulação"). **Estrita** credita só equivalentes; **branda** credita também as parciais. A tabela item a item está em `comparacao_detalhada.json`.

| Variante | Leitura | TP | FP | FN | Precisão | Revocação | F1 condicional |
|---|---|---:|---:|---:|---:|---:|---:|
| base | estrita | 1 | 24 | 30 | 4,0% | 3,2% | 3,6% |
| base | branda | 7 | 18 | 24 | 28,0% | 22,6% | 25,0% |
| adaptado | estrita | 8 | 41 | 23 | 16,3% | 25,8% | 20,0% |
| adaptado | branda | 15 | 34 | 16 | 30,6% | 48,4% | 37,5% |

Parciais: base 6, adaptado 7. Por família (TP/FP/FN, estrita): 45975308 0/0/9 nas duas; 65439381 base 1/15/8, adaptado 5/12/4; 74045448 base 0/9/5, adaptado 0/7/5; 80949080 base 0/0/8, adaptado 3/22/5.

Somando as duas famílias de desenvolvimento (números da análise 08d × 08c, que não tinham o conceito de parcial): base TP 10, FP 37, FN 35; adaptado TP 14, FP 70, FN 31 nas seis famílias.

## O que o 08d acertou

- Funções com alvo preservado em 65439381 (adaptado): "tratar dor ou irritação em uma articulação" e "lubrificação das articulações" exatas.
- Materiais separados conforme D3 em 65439381 (adaptado): lipossomas, GPL e SM como itens distintos.
- 80949080 (adaptado): estrutura metálica, estrutura capilar e camada externa de revestimento corretas.
- Todas as respostas aceitas passaram na validação estrutural de trechos. Isso não comprova suporte semântico.

## Problemas persistentes

- **Memes por partes e propriedades (D1):** 65439381 e 74045448 listam fosfolipídio, cadeia de hidrocarboneto, esfingomielina, temperatura de transição de fase, domínios isolados e "atividade nuclease deficiente" como memes. 80949080 (adaptado) lista 9 memes sem correspondência, com rótulos genéricos ("disposição construtiva") e materiais.
- **Convergência sem suporte:** 10 pares propostos em fluxos válidos (65439381: 4; 74045448: 4; 80949080 adaptado: 2), todos parte–todo ou objeto/propriedade. A referência não tem pares positivos: cada um é falso positivo condicional, e a revocação de pares é indefinida, não zero.
- **Efeitos (D4):** 10 efeitos propostos, nenhum com correspondência (a referência tem 1 efeito, em 45975308, que nenhuma variante produziu). 6 deles ligam-se a uma função, e 4 usam categorias de custo/eficiência sem suporte textual.
- **Cobertura:** em 74045448 as duas variantes entregam materiais e processos vazios (a referência tem 2 materiais e 1 processo). A base de 80949080 entrega tudo vazio mesmo com estrutura clara no texto.
- **Limite de saída:** 45975308 foi interrompida por excesso de enumeração antes de fechar o JSON, não por tamanho da entrada. Os 9 itens de referência dessa família ficam sem nenhuma recuperação.

## Limites desta análise

Um anotador; referência com **zero pares positivos**; mapeamento feito pelo assistente (as parciais dependem de julgamento, daí as duas leituras); famílias já vistas em 08/08b; regras nascidas de outras duas famílias. Sem média macro nem significância. A referência e os prompts não foram alterados depois de ver os resultados.

## Decisões em aberto

1. Variante de produção: **não decidir** com estes dados. Registrar o critério (por exemplo, F1 estrito em famílias novas + taxa de fluxos válidos) antes de nova rodada.
2. O limite de 1.024 tokens de saída corta famílias com muitos materiais; mudá-lo é novo protocolo, não edição do 08d.
3. D1–D5 não corrigiram propriedades/partes como memes nem efeitos duplicados nestas famílias. Mais engenharia de prompt exige nova rodada em famílias ainda não usadas, sem tratar estas quatro como não vistas.
