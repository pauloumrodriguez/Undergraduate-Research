# STATUS — replicação LLM-EIDT, piloto brasileiro PATSTAT

Atualização de 19/11/2026. Fonte da especificação: `.claude/skills/llm-eidt-spec/SKILL.md`, que separa fatos do artigo e decisões de replicação. Este arquivo descreve o estado real do repositório. A versão anterior (auditoria de 19/11/2026, antes da rodada 08d nas quatro famílias, da referência v3 e do EDh) está em `historico/antes_status_readme_20261119/STATUS.md`.

## Resumo

O pipeline está implementado e executado até o **nível micro, etapa de extração (IE)**, em fase de desenvolvimento. Há também uma implementação testada em CPU do rótulo DP/CP (Eq. 14), do EDh (Eq. 15) e de P/R/F1/NDCG, validada contra as Tabelas 6–9 do artigo, mas sem dados reais de entrada.

**Não há código** para: alinhamento semântico (eLCPM), filtro de novidade (Eq. 13), agrupamento em temas (Algoritmo 2) e Dh.

O benchmark Dh está **bloqueado por dados**: o pacote PATSTAT não contém citações, datas de publicação nem histórico anterior a 2010.

Decisão do pesquisador em 19/11/2026: seguir **sem adjudicação humana** da comparação 08d × referência v3 por enquanto. A análise assistida por IA permanece sem verificação independente.

## Resultados principais

| Tema | Resultado |
|---|---|
| Ajuste CPC | Perda de validação 4,3738 → 0,6002. Validação: base 0/20, adaptado 1/20. Teste: 0/20 nas duas. Formato válido 1/20 × 20/20. O adaptador aprendeu o formato, não o código. |
| Extração 08d, 2 famílias (desenvolvimento) | 4/4 fluxos válidos. F1 condicional: base 50,0%, adaptado 24,5% (14 itens). |
| Extração 08d, 4 famílias novas (`resultados/etapa_5e/`) | 6/8 fluxos válidos (adaptado 3/4, base 2/4). 45975308 estourou 1.024 tokens de saída nas duas variantes; base de 80949080 falhou o schema de relações. F1 condicional sobre 31 itens: base 3,6% (estrita) a 25,0% (branda); adaptado 20,0% a 37,5%. 10 pares e 10 efeitos propostos, nenhum com correspondência. |
| Referência v3 | 6 famílias, 45 itens, um anotador, **zero pares de convergência** (`resultados/etapa_5e/piloto_br_200/referencia_consolidada_20261119_v3/`). |
| EDh e métricas | 23 testes. Contra o artigo: P/R/F1 batem em 2/3 janelas pela regra escrita; a Tabela 7 só bate com um corte gráfico inferido; o NDCG publicado não é reproduzível (`docs/EDH_METRICAS_V1.md`, `resultados/etapa_6/`). |

O adaptado ficou atrás da base nas 2 famílias de desenvolvimento e à frente nas 4 novas. Com esse tamanho e uma referência de um anotador, isso é compatível com ruído; não há base para escolher variante.

## 1. Inventário

### Documentação
| Arquivo | Conteúdo |
|---|---|
| `README.md` | Visão do piloto, estado atual e próximos passos (atualizado em 19/11/2026). |
| `docs/ADAPTACAO_METODOLOGICA_BR.md` | População BR, recorte CPC A61/C12N, unidade família DOCDB, partições, idiomas, lacunas × tratamento. |
| `config/experimento.json` | Blocos `publicado`, `adotado`, `pendente`, `piloto`. Congelado. |
| `docs/TESTE_QLORA_GPU.md`, `AJUSTE_QLORA_1024.md`, `TREINAMENTO_QLORA_CPC.md` | Diagnóstico de GPU, QLoRA NF4/FP16 com 1.024 tokens, treino CPC. |
| `docs/AVALIACAO_CPC_E_PROXIMAS_ETAPAS.md`, `AVALIACAO_FINAL_CPC_07.md` | Protocolos congelados de avaliação CPC. |
| `docs/EXTRACAO_E_REVISAO_08.md` … `08D.md` | Protocolos de extração v1–v4 e revisão humana. |
| `docs/EXTRACAO_E_REVISAO_08D_VALIDACAO4.md`, `VALIDACAO_ENTREGA_08D_VALIDACAO4.md` | Rodada do 08d nas quatro famílias novas e verificação local. |
| `docs/REGRAS_EXTRACAO_D1_D5_V1.md` | Regras humanas D1–D5 dos prompts v4. |
| `docs/EDH_METRICAS_V1.md` | EDh, rótulo DP/CP, P/R/F1/NDCG e validação contra as Tabelas 6–9. |
| `historico/`, `entregas/` | Instantâneos com SHA-256; ZIPs de atualização e pacotes de revisão humana. |

### Dados
| Artefato | Estado |
|---|---|
| `dados/brutos/patstat_br_1000/` | Pacote original de 1.000 famílias, SHA-256 fixado. |
| `dados/processados/piloto_br_200/` | 200 famílias congeladas (960 elegíveis; 67/67/66 por janela; 160/20/20) e `preprocessado/`. |
| `dados/referencia/` | Artigo v1 (PDF), notebook de extração PATSTAT original e `tabelas_6_8_artigo_transcritas.json`. |

### Código e notebooks
| Etapa | Notebook | Script / config |
|---|---|---|
| 00–03 | `00_…`, `01_…`, `02_selecionar_200_patstat_br`, `03_preprocessar_patstat_br` | `scripts/selecionar_piloto_br.py`, `preprocessar_patstat_br.py`, `schemas/`, `prompts/` |
| 04/04b, 05 | Teste QLoRA, treino CPC | `testar_qlora_gpu.py`, `treinar_qlora_cpc.py`, `config/perfil_treino_qlora_1024.json` |
| 06, 07 | Avaliação CPC (validação, teste) | `avaliar_cpc_geracao.py`, `avaliar_cpc_teste.py` |
| 08, 08b, 08c, 08d | Extração v1–v4 | `extrair_evidencias.py`, `_v2.py`, `_v3.py`, `_v4.py`; perfis em `config/` |
| 08d, 4 famílias | `08d_extrair_evidencias_validacao4.ipynb` | `extrair_evidencias_v4_validacao4.py`, `config/perfil_extracao_validacao4_v4.json` |
| EDh e métricas | — | `scripts/edh_metricas.py`, `scripts/validar_metricas_artigo.py`, `tests/test_edh_metricas.py` |

`02_registrar_coleta_e_selecionar_200.ipynb` (783 bytes) e `selecionar_piloto.py` são resíduos de versões anteriores.

### Resultados
| Pasta | Conteúdo |
|---|---|
| `resultados/etapa_1/` a `etapa_4/` | Tokenizador, treino 05, CPC validação e teste. |
| `resultados/etapa_5/`, `5b/`, `5c/`, `5d/` | Extrações 08 a 08d e referência v2 (2 famílias, 14 itens). |
| `resultados/etapa_5e/piloto_br_200/` | Execução 08d nas 4 famílias, referência v3 e análise (`analise_08d_validacao4_v1/`). |
| `resultados/etapa_6/validacao_metricas_artigo_v1/` | Recálculo da Tabela 9 a partir das Tabelas 6–8. |

## 2. Status etapa por etapa

Legenda: ✅ concluído · 🟡 parcial · ⬜ não iniciado · ⛔ bloqueado por dados.

| # | Etapa do artigo | Status | Observações |
|---|---|---|---|
| 1 | Coleta e dados (§4.1, §4.3) | ✅ adaptado | 200 famílias BR em vez de 14.265 patentes CN. Sem citações, publicação ou histórico pré-2010. |
| 2a | Micro: LoRA | ✅ executado, efeito nulo no alvo | Qwen3-8B QLoRA NF4, 1.024 tokens. CPC proxy no teste: 0/20. O artigo não reporta a métrica CPC. |
| 2b | Micro: extração IE | 🟡 | Fluxos válidos 6/8 nas 4 famílias novas, mas F1 condicional baixo. Referência de um anotador, sem pares positivos. Teste reservado não usado. |
| 2c | Micro: alinhamento eLCPM | ⬜ | Sem código de e5, UMAP, k-means ou prompt A.2. `k = 50` é inviável para ~200 famílias. |
| 3a | Meso: filtro de novidade (Eq. 13) | ⬜ | Regra decidida: primeira aparição na amostra; empates = todos novos. |
| 3b | Meso: rótulo DP/CP (Eq. 14) | 🟡 | `rotulo_dp` implementada e testada como função booleana; falta formalizar o `C_std` (efeito vinculado a material/fluxo novo) e a entrada real. |
| 4a | Macro: temas (Alg. 2) | ⬜ | `k`, composição do vetor e uso global × por janela não decididos. |
| 4b | Macro: EDh (Eq. 15) | ✅ implementado e testado | Sem dados reais de entrada. Invariante da ablação sem `C_conv` testado. |
| 5 | Benchmark Dh | ⛔ | Artigo não dá fórmula e cita "Yang et al., 2023", ausente das referências. Pacote sem citações. Não fabricar valores. |
| 6a | Avaliação de componentes (IE) | 🟡 | Condicional; referência exposta; análise assistida por IA, sem adjudicação (adiada por decisão do pesquisador). |
| 6b | Avaliação temática (P/R/F1 + NDCG) | ✅ implementado e validado em CPU | Sem Dh próprio. NDCG do artigo não reproduzível (Tabela 7 com temas repetidos e ausentes; valores de 2010–14 e 2020–24 não batem). |

## 3. O que falta

Decisões novas devem ser registradas antes de observar o resultado que elas afetam, em perfil versionado e `docs/`, sem editar arquivos congelados.

### A. Extração (2b)
1. Decidir a variante de produção (base × adaptado) e o critério, antes de novos dados. Não há evidência para escolher.
2. Se houver nova rodada: famílias ainda não usadas, referência anotada **antes** das previsões, de preferência com dois anotadores e adjudicação, incluindo casos com pares de convergência positivos.
3. Decidir o limite de 1.024 tokens de saída (cortou 45975308): mudança exige novo protocolo, não edição do 08d.
4. Medir tempo e memória na T4 (pico reservado 12,56 de 14,56 GiB; 1.135 s para 14 chamadas).
5. Executar nas 200 famílias só depois de qualidade aceitável (400 chamadas).

### B. eLCPM, C. meso, D. macro
- Alinhamento: embeddings e5, UMAP, k-means e prompt A.2 com validador; faixa de `k`; alinhamento de relações derivado dos memes alinhados.
- Eq. 13 sobre elementos alinhados e formalização do `C_std`, com testes.
- Temas (Alg. 2): vetor, `k`, nomeação A.3, temas globais ou por janela.

### E. Dh — bloqueio principal
- Adquirir do PATSTAT: citações para frente datadas (família DOCDB), datas de publicação e histórico 2000–2009 do mesmo recorte.
- Definir e documentar a fórmula do Dh (por exemplo CD/DI de Funk & Owen-Smith) e a agregação por tema. Incluir sensibilidade com horizonte igual entre coortes.

### F. Avaliação temática
- Ligar `edh_metricas.py` às saídas reais quando existirem.
- Pedir aos autores a implementação do NDCG e a Tabela 7 completa; até lá, tratar o NDCG publicado como não reproduzível.

### G. Ablações e baselines
- "Sem LoRA" (base) já é comparável na extração. As demais dependem de C a F.

## 4. Riscos que afetam a interpretação

- **Tamanho:** 200 famílias contra 14.265. Temas, EDh e NDCG terão variância alta.
- **Adaptador CPC sem ganho:** 0/20 no teste; na extração, atrás da base em 2 famílias e à frente em 4. Não cumpre o papel de adaptação de domínio nesta escala.
- **Referência de extração:** 45 itens, 6 famílias, um anotador, regras formuladas a partir de 2 delas, anotação das 4 novas por quem conhecia as regras, famílias já vistas em 08/08b, zero pares positivos. Não sustenta conclusões sobre convergência, insumo central do EDh.
- **Mapeamento assistido por IA:** as parciais da análise 08d × v3 dependem de julgamento; por isso há leituras estrita e branda. Sem adjudicação humana.
- **Vazamento temporal:** Qwen3 é posterior às janelas. Temas globais usariam informação posterior.
- **Dh:** sem dados, nenhuma validação ex-post é possível. Qualquer EDh isolado é descritivo.
- **Artigo:** Dh sem fórmula, NDCG não definido nem reproduzível, Tabela 7 inconsistente. A replicação numérica das Tabelas 6–11 não é garantida mesmo com os dados.
