# STATUS — replicação LLM-EIDT, piloto brasileiro PATSTAT

Auditoria de 19/11/2026. Fonte da especificação: `.claude/skills/llm-eidt-spec/SKILL.md`, que separa fatos do artigo e decisões de replicação. Este arquivo descreve o estado real do repositório. Nenhum arquivo existente foi alterado.

## Resumo

O pipeline está implementado e executado até o **nível micro, etapa de extração (IE)**, e ainda em fase de desenvolvimento. Os dados, o ajuste LoRA/CPC e um extrator em duas etapas com gramática JSON e regras humanas D1–D5 existem e foram executados no Colab (T4).

**Não há código** para:

- alinhamento semântico (eLCPM);
- filtro de novidade (Eq. 13);
- rotulagem DP/CP (Eq. 14);
- agrupamento em temas (Algoritmo 2);
- EDh (Eq. 15);
- Dh;
- métricas temáticas (P/R/F1/NDCG).

Uma busca por `edh|ndcg|umap|elcpm|Dh` em `scripts/` não retorna ocorrências.

O benchmark Dh está **bloqueado por dados**: o pacote PATSTAT não contém citações, datas de publicação nem histórico anterior a 2010.

## 1. Inventário do que está pronto

### Documentação

| Arquivo | Conteúdo |
|---|---|
| `README.md` | Visão do piloto e fluxo 00–10. **Desatualizado:** indica o 07 como próximo passo e o 08 "a preparar", mas 08–08d já foram entregues e executados. |
| `docs/ADAPTACAO_METODOLOGICA_BR.md` | População BR, recorte CPC A61/C12N, unidade família DOCDB, partições, idiomas, tabela de lacunas × tratamento. |
| `config/experimento.json` | Blocos `publicado` (artigo), `adotado` (decisões: EDh, corte por média, NDCG reconstruído, controle da Tabela 7, invariante da ablação, novidade, Dh), `pendente`, `piloto`. |
| `docs/TESTE_QLORA_GPU.md`, `docs/AJUSTE_QLORA_1024.md`, `docs/TREINAMENTO_QLORA_CPC.md` | Diagnóstico de GPU, mudança para QLoRA NF4/FP16 com 1.024 tokens, treinamento CPC. |
| `docs/AVALIACAO_CPC_E_PROXIMAS_ETAPAS.md`, `docs/AVALIACAO_FINAL_CPC_07.md` | Protocolos congelados de avaliação CPC (validação e teste). |
| `docs/EXTRACAO_E_REVISAO_08.md` … `08D.md` | Protocolos de extração v1–v4, revisão humana e regras de correspondência. |
| `docs/REGRAS_EXTRACAO_D1_D5_V1.md` | Regras humanas D1–D5 incorporadas nos prompts v4. |
| `docs/VALIDACAO_ENTREGA_*.md` | Verificações locais em CPU de cada entrega. |
| `historico/` | Instantâneos e manifestos SHA-256 antes de cada revisão. |
| `entregas/` | ZIPs de atualização 08c/08d e pacotes de revisão humana. |

### Dados

| Artefato | Estado |
|---|---|
| `dados/brutos/patstat_br_1000/LLM_EIDT_LORA_1000.zip` + `proveniencia.json` | Pacote original de 1.000 famílias, SHA-256 fixado. |
| `dados/processados/piloto_br_200/piloto_200.csv` + `auditoria.json` | 200 famílias congeladas (960 elegíveis A61/C12N; 67/67/66 por janela; 160/20/20). |
| `dados/processados/piloto_br_200/preprocessado/` | `entradas_extracao.jsonl`, `metadados.jsonl`, `treino/validacao/teste_cpc.jsonl`, auditoria do pré-processamento. |
| `dados/referencia/` | Artigo v1 (PDF) e notebook de extração PATSTAT original. |

### Código e notebooks

| Etapa | Notebook | Script / config |
|---|---|---|
| 00 Preparação e auditoria de insumos | `00_preparar_drive_e_auditar_insumos.ipynb` | `config/insumos*.csv` |
| 01 Diagnóstico GPU/modelos | `01_validar_gpu_e_modelos.ipynb` | — |
| 02 Seleção das 200 | `02_selecionar_200_patstat_br.ipynb` (há também um `02_registrar_coleta_e_selecionar_200.ipynb` de 783 bytes, resíduo da versão anterior) | `scripts/selecionar_piloto_br.py` (`selecionar_piloto.py` é a versão antiga) |
| 03 Pré-processamento | `03_preprocessar_patstat_br.ipynb` | `scripts/preprocessar_patstat_br.py`, `schemas/extracao_patstat_br*.json`, `prompts/extracao_patstat_br*.txt` |
| 04/04b Teste QLoRA | `04_testar_qlora_gpu.ipynb`, `04b_testar_qlora_1024.ipynb` | `scripts/testar_qlora_gpu.py`, `config/perfil_qlora_teste*.json` |
| 05 Treino CPC | `05_treinar_qlora_cpc.ipynb` | `scripts/treinar_qlora_cpc.py`, `config/perfil_treino_qlora_1024.json` |
| 06 Avaliação CPC (validação) | `06_avaliar_cpc_validacao.ipynb` | `scripts/avaliar_cpc_geracao.py`, `config/perfil_avaliacao_cpc_validacao.json` |
| 07 Avaliação CPC (teste) | `07_avaliar_cpc_teste.ipynb` | `scripts/avaliar_cpc_teste.py`, `config/perfil_avaliacao_cpc_teste.json` |
| 08 Extração v1 | `08_extrair_evidencias_piloto.ipynb` | `scripts/extrair_evidencias.py`, `config/perfil_extracao_validacao6.json` |
| 08b Extração v2 | `08b_extrair_evidencias_piloto.ipynb` | `scripts/extrair_evidencias_v2.py`, `config/perfil_extracao_validacao6_v2.json` |
| 08c Extração v3 (2 etapas + gramática) | `08c_extrair_evidencias_etapas.ipynb` | `scripts/extrair_evidencias_v3.py`, `prompts/*_v3.txt`, `schemas/extracao_etapas_v3.templates.json`, `requirements_extracao08c.txt` |
| 08d Extração v4 (regras D1–D5) | `08d_extrair_evidencias_regras.ipynb` | `scripts/extrair_evidencias_v4.py`, `prompts/*_v4.txt`, `config/perfil_extracao_validacao2_v4.json` |

### Resultados

| Pasta | Conteúdo |
|---|---|
| `resultados/etapa_1/` | Validações de tokenizador e conferência dos notebooks 02/03. |
| `resultados/etapa_2/` | Relatórios do treino 05 (3 épocas, 30 atualizações, perda de validação 4,3738 → 0,6002; checkpoint `passo_000030`). |
| `resultados/etapa_3/` | CPC validação: base 0/20, adaptado 1/20; formato válido 1/20 × 20/20. |
| `resultados/etapa_4/` | CPC teste: base 0/20, adaptado 0/20; formato válido 1/20 × 20/20. |
| `resultados/etapa_5/`, `etapa_5b/` | Extrações 08 e 08b (6 famílias de validação, 12 gerações cada; nenhuma aprovada). |
| `resultados/etapa_5c/` | Comparação humana 08c e **referência consolidada v2** (2 famílias, 14 itens, decisões D1–D5). |
| `resultados/etapa_5d/` | Extração 08d (8 chamadas, 4 fluxos válidos) e análise 08d × 08c. |

## 2. Status etapa por etapa

Legenda: ✅ concluído · 🟡 em desenvolvimento/parcial · ⬜ não iniciado (só especificado) · ⛔ bloqueado por dados.

| # | Etapa do artigo | Status | Evidência no repositório | Observações |
|---|---|---|---|---|
| 1 | Coleta e dados (§4.1, §4.3) | ✅ adaptado | `dados/`, `scripts/selecionar_piloto_br.py`, `scripts/preprocessar_patstat_br.py`, `auditoria*.json` | 200 famílias BR em vez de 14.265 patentes CN. Sem citações, publicação ou histórico pré-2010. |
| 2a | Micro: LoRA (§3.1.1, §4.2) | ✅ executado, com efeito nulo no alvo | etapas 2–4 | Qwen3-8B QLoRA NF4, 1.024 tokens. CPC proxy no teste: 0/20 nas duas variantes. O adaptador só aprendeu o formato. O artigo não reporta a métrica CPC. |
| 2b | Micro: extração IE (§3.1.2, A.1) | 🟡 desenvolvimento | etapas 5–5d, scripts v1–v4 | 08d: 4/4 fluxos estruturalmente válidos em 2 famílias. F1 condicional: base 50,0%, adaptado 24,5% (14 itens de referência, 0 pares positivos). Não rodado nas 200. Teste reservado ainda não usado. |
| 2c | Micro: alinhamento eLCPM (§3.1.3, Alg. 1, A.2) | ⬜ | `experimento.json → piloto.alinhamento` ("Planejado") | Sem código de e5, UMAP, k-means ou prompt A.2. |
| 3a | Meso: filtro de novidade (Eq. 13) | ⬜ | `adotado.historico` | Regra decidida: primeira aparição observada na amostra; empates = todos novos. |
| 3b | Meso: rótulo DP/CP (Eq. 14) | ⬜ | `publicado.meso_e_macro.regra_dp` | Vínculo efeito ↔ material/fluxo do `C_std` a formalizar. |
| 4a | Macro: temas (Alg. 2, A.3) | ⬜ | `publicado.meso_e_macro.agrupamento_temas` | `k`, composição do vetor e uso global × por janela não decididos. |
| 4b | Macro: EDh (Eq. 15) | ⬜ especificado | `adotado.indices.edh`, `edh_sem_dp`, `corte_principal`, `controle_ablacao` | Totalmente especificado; falta implementar e testar. |
| 5 | Benchmark Dh | ⛔ | `adotado.indices.dh`, `sensibilidade_citacoes` | Artigo não dá fórmula. Pacote sem citações. Política: não fabricar valores. |
| 6a | Avaliação de componentes (P/R/F1 IE/SA/TC) | 🟡 só IE, condicional | `analise_08d_vs_08c_v1/RELATORIO.md` | Referência de 1 anotador exposto às previsões, mais assistência de IA. Sem anotação independente no teste. |
| 6b | Avaliação temática (P/R/F1 + NDCG) | ⬜ especificado | `adotado.indices.ndcg_reconstruido`, `controle_tabela_7` | Sem código. Depende de 4b e 5. |

## 3. O que falta para uma execução ponta a ponta

Ordem sugerida. Cada decisão nova deve ser registrada antes de observar o resultado que ela afeta: em perfil versionado e `docs/`, sem editar arquivos congelados.

### A. Fechar a extração (2b)

1. Decidir a variante de produção (base × adaptado) e a versão de prompt. O 08d favorece a base em 2 famílias, mas a evidência é fraca. Registrar o critério antes de novos dados.
2. Anotar **antes das previsões** novas famílias de validação; idealmente 2 anotadores com adjudicação. Incluir casos com pares de convergência positivos, hoje ausentes da referência.
3. Avaliar o procedimento congelado nessas famílias. Depois, uma única vez, no **teste reservado** (20 famílias) com anotação independente.
4. Executar o extrator congelado nas **200 famílias**: 400 chamadas (2 etapas × 200). Medir tempo e memória na T4 e registrar falhas sem convertê-las em ausência.

### B. Implementar eLCPM (2c)

5. Script de embeddings e5 (revisão fixada, prefixo definido), UMAP 2D e k-means com curva SSE. Decidir a faixa de `k`: `k = 50` do artigo é inviável para ~200 famílias.
6. Prompt A.2 em pt/en com validador: strings inalteradas, cada uma em exatamente um grupo, nenhuma sobra. Definir estratégia para clusters maiores que o contexto.
7. Definir o alinhamento de relações: recomendado derivar o par alinhado dos memes alinhados, coerente com `|R*_p|`. Definir também se materiais, fluxos e efeitos são alinhados separadamente.
8. Avaliar SA contra referência humana; o equivalente da Tabela 4 depende de anotação de alinhamento.

### C. Implementar meso (3a, 3b)

9. Função da Eq. 13 sobre os elementos alinhados, com ano de depósito do representante, empates e universo (amostra × janela) conforme `adotado.historico`. Escrever testes unitários.
10. Função da Eq. 14 com `C_conv`, `C_func` e `C_std`. Formalizar o `C_std`: material ou fluxo novo **vinculado** a efeito `reducao_custos`/`ganho_eficiencia`. Escrever testes unitários.

### D. Implementar macro (4a, 4b)

11. Algoritmo 2: vetor (título + memes alinhados), UMAP, k-means, nomeação A.3 e agrupamento em temas. Decidir `k`, número de temas e se os temas são globais ou por janela. Com ~67 famílias por janela, poucos temas e EDh baixos são esperados.
12. EDh conforme `adotado.indices`, com testes:
    - h-index básico;
    - `edh_sem_dp = 0`;
    - relações distintas;
    - invariante da ablação sem `C_conv`.

### E. Dh (5) — bloqueio principal

13. Adquirir do PATSTAT: citações para frente datadas (família DOCDB), datas de publicação e histórico 2000–2009 do mesmo recorte.
14. Definir e documentar a fórmula de Dh: índice por patente, por exemplo CD/DI de Funk & Owen-Smith, e agregação por tema. O artigo não a fornece e cita "Yang et al., 2023", ausente das referências. Incluir a sensibilidade com horizonte igual entre coortes.
15. Implementar Dh isolado das entradas do modelo.

### F. Avaliação temática (6b)

16. P/R/F1 com corte `≥ média` exata e NDCG conforme `ndcg_reconstruido` (ganho linear, empates pela média do bloco).
17. **Validar a implementação contra o artigo:** recalcular P/R/F1/NDCG a partir das Tabelas 6–8 e comparar com a Tabela 9. Registrar as duas leituras da Tabela 7 e verificar se a convenção de empates reproduz 0,9961 (2010–14).
18. Executar por janela e relatar os resultados como exploratórios, sem equivalência numérica com o artigo.

### G. Ablações e baselines (opcional para o primeiro ponta a ponta)

19. Sem LoRA (base) já é comparável na extração. Sem SA, sem TC e sem cada critério dependem de C–F.

### Pendências de documentação, sem alterar arquivos congelados

- O `README.md` está desatualizado em relação a 08–08d. Atualizar em entrega própria quando autorizado.
- `experimento.json → piloto.treino` descreve BF16/2.048 tokens; o executado foi QLoRA NF4/FP16/1.024 (`perfil_treino_qlora_1024.json`). A divergência está documentada nos perfis e docs, não no protocolo principal.
- Os `pendente.para_ajuste_e_extracao` de `experimento.json` (GPU, tokenizador, perfil) já foram resolvidos na prática pelos notebooks 04–08d, mas continuam listados como pendentes.

## 4. Riscos que afetam a interpretação

- **Tamanho:** 200 famílias contra 14.265 patentes. A estrutura de 16 temas × 3 janelas, os EDh e o NDCG terão alta variância.
- **Adaptador CPC sem ganho mensurável:** 0/20 no teste, e pior que a base na extração do 08d. O ajuste não cumpre o papel de adaptação de domínio do artigo nesta escala.
- **Referência de extração:** 14 itens, 2 famílias, revisada após ver previsões, sem pares positivos. Não sustenta conclusões sobre convergência, que é o insumo central do EDh.
- **Vazamento temporal:** Qwen3 é posterior às janelas. Temas globais usariam informação posterior.
- **Dh:** sem dados, nenhuma validação ex-post é possível. Qualquer resultado EDh isolado é descritivo.
