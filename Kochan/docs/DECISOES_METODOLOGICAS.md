# Decisões metodológicas

| Decisão | O original informa | Implementação desta camada | Estado |
|---|---|---|---|
| Corpus | USPTO-2M, 2.000.147 patentes, 2006–2015 | valida total, anos, IDs e hashes | confirmado em alto nível |
| Campos | título, resumo e ano | `Title`, `Abstract`, `Year` | confirmado |
| Limpeza | remoção de pontuação | `string.punctuation` | confirmado |
| Solr | uso do Apache Solr | snapshot v2, recursos e validação do índice vivo | original incompleto |
| Vocabulário | 148 termos finais | 148 posições, 147 conceitos únicos | ambíguo |
| Sinônimos | separados por `;`, combinados com OR | v01 preserva; sensibilidades isoladas | confirmado no TCC |
| Consulta | conceitos combinados com AND; frases ilustradas entre aspas | v01 usa frases exatas | campos/analisador não informados |
| Tempo da rede | armazenamento ano a ano; artigo diz “annual networks” | anual é reconstrução textual; cumulativa é diagnóstico | cumulativa não confirmada |
| Tabela 3 | 0 ausência, 1 presença | seis provas binárias | confirmado |
| Nós de 2006 | Figura 6 e total 50 | lista dos 50 rótulos recuperada | confirmado |
| Aresta | presença de coocorrência | peso é frequência; limiar >0 é hipótese | inferido |
| Ocultação | remove ligações | preservação de componentes e 20% são hipóteses | não informado |
| Negativos | ligações inexistentes | todos ou razão configurável | parcialmente informado |
| Node2vec | utilizado | parâmetros, sementes e hash estável em JSON/código | original incompleto |
| Operador de aresta | não informado | Hadamard na reconstrução | assumido |
| Classificador | regressão logística, 70/30 | perfil fixo, avaliação ligada por hashes | parcialmente confirmado |
| Repetições | 100 | 100 por ano | confirmado |
| Limiares | 0,50, 0,70 e 0,85 | mantidos | confirmado |
| Horizonte | 1, 3 e 5 anos | protocolo descrito; executor ainda ausente | incompleto |

Nenhuma variante pode ser chamada de “a configuração usada por Patrick” sem
código, banco de relações ou configuração original que a confirme.
