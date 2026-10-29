# Resultados das variantes de rede

Este documento resume os resultados; os valores canônicos estão em
`evidencias/comparacao_variantes.json` e
`evidencias/diagnostico_pos_hoc_figura6.json`.

## Hierarquia de evidências

1. instruções metodológicas escritas;
2. seis ligações binárias da Tabela 3;
3. 50 rótulos da Figura 6;
4. contagens anuais de nós e arestas;
5. proximidade agregada, somente como diagnóstico.

Uma variante não é promovida apenas por reduzir o erro agregado.

## Decisão

- **v01 anual:** reconstrução textual oficial.
- **v11 cumulativa:** melhor candidata empírica não ajustada.
- **v12 cumulativa:** rejeitada apesar do erro de 6,61%, pois perde a ligação
  `carbon composite — carbon material`.
- **v13 cumulativa:** contagens exatas e 50 nós de 2006 exatos, mas ajuste
  pós-hoc. Gate confirmatório bloqueado.

## Achado da Figura 6

A v11 possui todos os 50 nós publicados de 2006 e seis extras. Ao remover os
seis extras, a união cumulativa reproduz exatamente os totais de 2006, 2007 e
2008. Uma busca exaustiva entre os nós que aparecem depois encontrou um único
par adicional cuja exclusão mantém todos os anos exatos:
`carbon dioxide equivalent` e `carbon dioxide removal`.

O TCC e o artigo não contêm uma regra que autorize essas exclusões. O encaixe é
útil para localizar a provável divergência de vocabulário/consulta, mas não
identifica sozinho o código original.

## Proveniência

v01–v05 foram preservadas como execuções históricas; suas assinaturas não são
reproduzíveis pelo gerador final. v07 e v09–v12 corresponderam ao gerador
pré-finalização. A v13 é uma derivação determinística dos CSVs da v11 e guarda
os hashes das cinco redes de origem.
