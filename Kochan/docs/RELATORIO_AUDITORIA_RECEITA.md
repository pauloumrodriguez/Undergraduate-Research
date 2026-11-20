# Menu de Replicação — Receita auditada de Kochan

## 1. 📋 Mise en Place (ingredientes e especificações)

| Ingrediente | TCC/artigo | Cópia melhorada | Veredicto |
|---|---|---|---|
| Corpus | USPTO-2M, 2.000.147 patentes, 2006–2015 | Total, anos e IDs auditados | **Verificado** |
| Texto | título, resumo e ano; pontuação removida | campos e limpeza preservados | **Verificado em alto nível** |
| Vocabulário | 148 termos; sinônimos separados por `;` e unidos por OR | 148 posições, 147 conceitos únicos; ambiguidades catalogadas | **Parcialmente verificado** |
| Solr | mecanismo informado, sem receita completa | Solr 10/Java 21 local; schema, config, amostras e recursos capturados | **Implementação local verificada; original não verificável** |
| Redes | relações ano a ano; 3.719 registros entre 79 termos | variantes anuais, cumulativas e por campo | **Método original incompleto** |
| Nós/arestas | totais 2006–2010 e Figura 6 de 2006 | totais configurados; 50 rótulos da figura recuperados | **Verificado** |
| Node2vec/classificador | Node2vec, regressão logística, 70/30, 100 repetições | parâmetros versionados e sementes explícitas | **Publicado parcialmente** |
| Horizontes | 1, 3 e 5 anos; limiares 50%, 70%, 85% | protocolo documentado, executor temporal ainda ausente | **Incompleto** |

O snapshot Solr v2 não é apresentado como a configuração de Patrick. Ele
documenta com precisão a coleção local usada nesta replicação.

## 2. 🍳 Passo a passo da preparação

- [Fiel ao Original] Preservar título, resumo, ano e remoção de pontuação.
- [Fiel ao Original] Usar as 148 posições do apêndice como fonte do
  vocabulário, registrando a duplicata de `activated carbon`.
- [Ajustado/Diferente] Deduplicar para 147 conceitos na reconstrução textual,
  porque a Figura 6 mostra um único nó `activated carbon`.
- [Fiel ao Original] Combinar sinônimos por OR e conceitos por AND na v01.
- [Ajustado/Diferente] Testar frase exata, tokens AND, campos separados,
  aliases compartilhados e somente termo principal sem escolher
  silenciosamente.
- [Fiel ao Original] Tratar a coluna “Ligação” da Tabela 3 como classe binária.
- [Ajustado/Diferente] Validar a rede de 2006 também pelos 50 rótulos legíveis
  na Figura 6.
- [Ajustado/Diferente] Separar rede anual — favorecida pelo texto — de união
  cumulativa, usada apenas como hipótese diagnóstica.
- [Ajustado/Diferente] Ligar cada avaliação aos CSVs e ao resumo da geração por
  SHA-256.
- [Incompleto] Confirmar a identidade das arestas e pesos: o original não os
  publica.
- [Incompleto] Executar o classificador confirmatório: o gate permanece
  bloqueado.
- [Incompleto] Reproduzir a avaliação de horizontes 1/3/5: falta implementar e
  validar o executor temporal.

### Degustação das variantes

| Variante | Interpretação | Erro médio de contagens | Provas Tabela 3 | Leitura |
|---|---|---:|---|---|
| v01 anual | todos os sinônimos, frase, título/resumo | 17,06% | 6/6 | reconstrução textual preferencial |
| v03 anual | tokens AND | 63,93% | 6/6 | ampla demais e incompatível com o exemplo entre aspas |
| v05 anual | remove aliases compartilhados | 15,63% | 6/6 | remove dois conceitos; regra não publicada |
| v11 cumulativa | somente termo principal | 9,66% | 6/6 | melhor candidata empírica não ajustada |
| v12 cumulativa | termo principal, mesmo campo | 6,61% | 5/6 | rejeitada por prova positiva |
| v13 cumulativa | v11 menos oito termos inferidos | 0,00% | 6/6 | ajuste pós-hoc, proibido como confirmação |

A v13 reproduz também os 50 rótulos de 2006. Isso mostra que é possível
“acertar” os totais, mas não prova que a regra usada por Patrick tenha sido
descoberta. As oito exclusões foram inferidas dos próprios resultados:

- `carbon dioxide equivalent`;
- `carbon dioxide removal`;
- `emission factor`;
- `emission reduction`;
- `global warming potential`;
- `greenhouse gas`;
- `primary production`;
- `removal unit`.

## 3. 🔍 Ingredientes omitidos na receita original

O TCC e o artigo não especificam de modo suficiente:

- coleção/configset, versão e analisadores do Solr;
- expressão exata que combina `Title` e `Abstract`;
- se um conceito no título e outro no resumo contam como coocorrência;
- escaping, stopwords, stemming e normalização das consultas;
- tratamento de conceitos duplicados e aliases compartilhados;
- lista dos 79 termos que efetivamente formaram relações;
- limiar mínimo para criar aresta;
- uso do peso de coocorrência no grafo e no Node2vec;
- lista das 3.719 relações par-ano;
- regra exata de remoção de arestas para amostras positivas;
- geração/balanceamento de negativos;
- parâmetros completos do Node2vec e operador de representação de aresta;
- sementes, versões de bibliotecas e solver da regressão;
- definição operacional de acerto nos horizontes de 1, 3 e 5 anos;
- tratamento de execuções sem previsões.

O texto e o artigo chamam as redes de anuais e descrevem armazenamento “ano a
ano”. A interpretação cumulativa aproxima melhor os totais, mas não é
explicitamente ensinada pela receita original.

## 4. 👨‍🍳 Veredicto do chef

**Sim, há material suficiente para melhorar bastante a replicação. Não há
material suficiente para provar uma réplica idêntica.**

O melhor prato fiel à receita escrita é a v01 anual. O melhor prato empírico,
sem usar os totais como ingredientes de ajuste, é a v11 cumulativa. A v13
chega exatamente à apresentação publicada, mas foi empratada olhando a foto
final; portanto é diagnóstico de subdeterminação, não validação independente.

O classificador não deve ser recalibrado para “recuperar” o ROC-AUC publicado
enquanto a identidade da rede não estiver resolvida. O próximo ingrediente
decisivo é um artefato do autor, nesta ordem:

1. tabela `relation` ou CSVs das redes de 2006–2015;
2. lista dos 79 termos ativos;
3. consultas/código de construção da rede;
4. schema/configset Solr original;
5. código de amostragem, Node2vec e avaliação temporal.

Até que isso seja obtido, qualquer modelo executado sobre v11 ou v13 deve ser
rotulado como **exploratório**, nunca como reprodução confirmatória.
