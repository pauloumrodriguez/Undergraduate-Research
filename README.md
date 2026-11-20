# Undergraduate Research — Iniciação Científica

Este repositório reúne dois estudos independentes de replicação e adaptação de
artigos científicos na área de análise de patentes. Cada estudo fica em sua
própria pasta, com código, dados, documentação e README próprios. Eles não
compartilham scripts nem resultados, e podem ser lidos separadamente.

## Estrutura do repositório

```text
Undergraduate Research/
├── Kochan/      # Replicação independente de Kochan (TCC 2022 e artigo 2024)
└── LLM EIDT/    # Piloto brasileiro do LLM-EIDT com dados do PATSTAT
```

## Os dois estudos

### 1. Kochan — replicação independente de predição de ligações

Reconstrução melhorada, a partir do TCC (2022) e do artigo (2024) de Patrick
Kochan, de uma metodologia de redes de coocorrência e predição de ligações sobre
o corpus de patentes USPTO-2M.

- **Em resumo:** foi possível reconstruir o corpus, testar hipóteses de
  coocorrência e aproximar muito as contagens publicadas. Não foi possível
  confirmar que arestas, pesos e parâmetros são os do autor, porque esses
  elementos não foram publicados. A predição de ligações é, portanto,
  **exploratória**, e não uma reprodução confirmatória.
- **Tecnologias e dados:** Python, Solr, corpus USPTO-2M.
- **Documentação:** [`Kochan/README.md`](Kochan/README.md)

### 2. LLM EIDT — piloto brasileiro com PATSTAT

Adaptação ao contexto brasileiro de um estudo com LLMs, usando 200 famílias de
patentes com vínculo BR (depósitos de 2010–2024, recorte CPC A61 ou C12N) do
pacote PATSTAT. O piloto usa 160 famílias para treino, 20 para validação e 20
para teste.

- **Em resumo:** o pipeline roda até a extração de informação do nível micro,
  com ajuste fino de Qwen3-8B (QLoRA) para CPC. O cálculo do EDh e das métricas
  de identificação está implementado e testado. O alinhamento, o filtro de
  novidade, o agrupamento em temas e o Dh ainda não foram feitos. Nenhum
  resultado do piloto reproduz numericamente as tabelas do artigo original.
- **Tecnologias e dados:** Python, Qwen3-8B (QLoRA), embeddings, PATSTAT.
- **Documentação:** [`LLM EIDT/README.md`](<LLM EIDT/README.md>)

## Princípios comuns

- **Rigor científico antes de resultado bonito.** Resultados exploratórios são
  rotulados como tais. Ajustes feitos a partir dos próprios alvos não são
  apresentados como confirmação do método original.
- **Rastreabilidade.** Configurações, hashes e evidências são registrados, e
  versões anteriores de documentos ficam preservadas.
- **Limitações explícitas.** Cada pasta documenta o que foi e o que não foi
  possível reproduzir, e por quê.

## Como navegar

1. Leia este arquivo para entender a divisão entre os dois estudos.
2. Abra o README da pasta de interesse e siga a seção "Por onde começar" (Kochan)
   ou "Estado atual" (LLM EIDT).
3. Consulte a pasta `docs/` de cada estudo para metodologia, protocolos e
   veredictos.

## Referências

KOCHAN, Patrick Davila. **Um método de análise de patentes voltado à previsão
de tecnologias**. 2022. 38 p. Trabalho de Conclusão de Curso (Graduação em
Engenharia de Computação) – Centro de Ciências, Tecnologias e Saúde do Campus
Araranguá, Universidade Federal de Santa Catarina, Araranguá, 2022.
Orientador: Alexandre Leopoldo Gonçalves.

KOCHAN, Patrick D.; BARCELOS, Bartholomeo O.; GONÇALVES, Alexandre L.
Identifying technological trends: a patent analysis method for technology
forecasting. In: SIMPÓSIO BRASILEIRO DE BANCO DE DADOS (SBBD), 39., 2024,
Florianópolis. **Anais** [...]. Porto Alegre: SBC, 2024. p. 327-340.

DING, Fangyuan; LU, Dongyuan. **Ex-ante identification of disruptive
technologies from patent text via LLM-based semantic evidence aggregation**.
Research Square, 20 maio 2026. Preprint. DOI: 10.21203/rs.3.rs-9585548/v1.

Os métodos replicados nas duas pastas pertencem aos autores dos artigos acima.
Este repositório é uma replicação e adaptação independente, sem vínculo com eles.

## Autoria

Paulo Ubiratan Muniz Rodrigues — Iniciação Científica, Universidade de São Paulo.
Contato: pauloumrodriguez@gmail.com

Orientador: Prof. Dr. Esteban Tuesta
Contato: tuesta@usp.br
