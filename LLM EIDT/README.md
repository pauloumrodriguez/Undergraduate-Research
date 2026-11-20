# LLM-EIDT — piloto brasileiro PATSTAT, 200 famílias

Adaptação do estudo ao contexto brasileiro: famílias com vínculo BR, depósitos de 2010–2024 e recorte CPC A61 ou C12N disponível no pacote PATSTAT. O piloto preserva 160 famílias de treino, 20 de validação e 20 de teste. Metodologia e limitações: `docs/ADAPTACAO_METODOLOGICA_BR.md`. Estado detalhado, lacunas e riscos: `STATUS.md`.

## Estado atual (19/11/2026)

O pipeline roda até a **extração de informação** do nível micro, e o cálculo do EDh e das métricas de identificação está implementado e testado em CPU. Não há ainda alinhamento (eLCPM), filtro de novidade, agrupamento em temas nem Dh. Nenhum resultado do piloto reproduz numericamente as Tabelas 2–11 do artigo.

- **Ajuste CPC (05, 06, 07):** 3 épocas, 30 atualizações, Qwen3-8B QLoRA NF4/FP16. A perda de validação caiu de 4,3738 para 0,6002. Na geração livre o ajuste aprendeu o formato (20/20 contra 1/20) mas não o código: validação base 0/20 e adaptado 1/20; teste 0/20 nas duas variantes.
- **Extração (08 a 08d):** quatro versões do procedimento. A 08d, com instruções D1–D5 congeladas, completou 4 de 4 fluxos em 2 famílias de desenvolvimento e 6 de 8 em 4 famílias novas de validação (`resultados/etapa_5e/`). F1 condicional nas 4 novas: 25,0% (base) e 37,5% (adaptado) pela leitura branda, 3,6% e 20,0% pela estrita. Referência v3: 6 famílias, 45 itens, um anotador, sem pares de convergência (`resultados/etapa_5e/piloto_br_200/referencia_consolidada_20261119_v3/`).
- **EDh e métricas (`scripts/edh_metricas.py`):** implementação testada (23 testes) e validada contra as Tabelas 6–9 do artigo: P/R/F1 batem em 2 de 3 janelas pela regra escrita; o NDCG publicado não é reproduzível (`docs/EDH_METRICAS_V1.md`, `resultados/etapa_6/`).
- **Bloqueio:** o benchmark Dh exige citações datadas, datas de publicação e histórico 2000–2009, que o pacote não tem.

A partição de teste (20 famílias) permanece reservada para extração. A adjudicação humana da comparação 08d × referência v3 foi adiada por decisão do pesquisador.

## Próximos passos possíveis

1. Decidir com o orientador se o piloto continua com os dados atuais ou se vale obter citações e histórico no PATSTAT completo.
2. Se continuar a extração: nova rodada somente em famílias ainda não usadas, com critério de seleção registrado antes; não reutilizar as seis famílias como se fossem não vistas.
3. Implementar o alinhamento, o filtro de novidade (Eq. 13) e o agrupamento em temas, que alimentam o EDh.
4. Pedir aos autores a implementação do NDCG e a Tabela 7 completa.

## Fluxo do projeto

| Etapa | Estado e finalidade |
|---|---|
| 00, 02, 03 | Preparação, seleção e textos pt/en concluídos |
| 01 e 04b | Diagnóstico de GPU e teste QLoRA concluídos |
| 05 | Treinamento CPC concluído; checkpoint da época 3 selecionado |
| 06, 07 | Avaliação CPC em validação e teste concluída |
| 08, 08b, 08c, 08d | Extração: quatro versões; 08d em duas e em quatro famílias (`notebooks/08d_extrair_evidencias_validacao4.ipynb`) |
| EDh e métricas | Implementados e validados (CPU); sem dados reais de entrada |
| 09 | A fazer: embeddings E5 e alinhamento dos elementos extraídos |
| 10 | A fazer: filtro de novidade, rótulo DP/CP, temas e análise dos limites do piloto |

Protocolos: `docs/AVALIACAO_CPC_E_PROXIMAS_ETAPAS.md`, `docs/AVALIACAO_FINAL_CPC_07.md`, `docs/EXTRACAO_E_REVISAO_08*.md`, `docs/EXTRACAO_E_REVISAO_08D_VALIDACAO4.md`, `docs/REGRAS_EXTRACAO_D1_D5_V1.md`, `docs/EDH_METRICAS_V1.md`. As etapas 09 e 10 são planejamento, não arquivos executáveis entregues.

## Rastreabilidade e limites

`config/experimento.json` e os dados preparados permanecem congelados. Perfis adicionais registram as escolhas computacionais e de avaliação. O índice `SHA256SUMS.txt` identifica os arquivos fixos das entregas; novos resultados de execução não entram automaticamente nesse índice. Versões anteriores de README, STATUS e do índice ficam em `historico/`. Não edite hashes para contornar uma divergência.

O CPC proxy não é classificação principal oficial nem anotação de extração. Nenhuma taxa de acerto CPC demonstra, por si só, a qualidade dos seis campos de extração. As métricas de extração são condicionais a uma referência pequena, de um anotador, anotada por quem conhecia as regras e sem pares positivos.

Os textos podem vir de membros diferentes da família, e o pacote não conserva a origem de cada título/resumo, edição PATSTAT, data da extração, citações ou datas de publicação. As métricas que dependem desses insumos exigem dados adicionais ou uma delimitação explícita da análise exploratória. O piloto brasileiro não reproduz automaticamente os resultados numéricos do corpus chinês.
