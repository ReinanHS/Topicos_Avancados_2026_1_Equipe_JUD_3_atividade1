---
sidebar_position: 1
---

# Visão geral da avaliação

A avaliação mede o desempenho dos modelos nas tarefas propostas, utilizando duas
estratégias distintas conforme o tipo de dataset. Cada estratégia foi escolhida
de acordo com a natureza das respostas geradas: respostas discursivas (texto
livre) ou respostas objetivas (múltipla escolha).

## Estratégias de avaliação

### Avaliação cruzada (Pairwise Metrics)

O dataset `oab_bench` contém questões discursivas da segunda fase da OAB, cujas
respostas são textos livres. Como não existe um gabarito exato para esse tipo de
questão, a avaliação é feita de duas formas complementares:

1. **Modelo vs Modelo**: compara as respostas geradas por cada par de modelos
   entre si, utilizando todas as combinações possíveis.
2. **Modelo vs Guideline**: compara as respostas de cada modelo contra as
   guidelines de referência fornecidas pelo próprio dataset.

As métricas utilizadas nessa estratégia são:

| Métrica         | O que mede                                                                    |
|-----------------|-------------------------------------------------------------------------------|
| **BLEU**        | Sobreposição de n-gramas entre a predição e a referência                      |
| **ROUGE-1**     | Sobreposição de unigramas                                                     |
| **ROUGE-2**     | Sobreposição de bigramas                                                      |
| **ROUGE-L**     | Maior subsequência comum entre os textos                                      |
| **BERTScore**   | Similaridade semântica baseada em embeddings contextuais (F1)                 |

A avaliação é feita **por turno** (cada subitem da questão é avaliado
separadamente) e ao final é calculada uma **média agregada** de todos os turnos.

Para mais detalhes sobre cada métrica, consulte a seção
[Métricas](./metrics/accuracy-precision.md).

### Avaliação exata (Exact Match)

O dataset `oab_exams` contém questões objetivas de múltipla escolha da primeira
fase da OAB, onde cada questão possui uma única alternativa correta. A avaliação
compara diretamente a letra escolhida pelo modelo com o gabarito oficial.

As métricas utilizadas nessa estratégia são:

| Métrica        | O que mede                                                                 |
|----------------|----------------------------------------------------------------------------|
| **Acurácia**   | Proporção de respostas corretas sobre o total                              |
| **Precisão**   | Capacidade do modelo de acertar quando escolhe uma alternativa (macro)     |
| **Recall**     | Capacidade do modelo de identificar a alternativa correta (macro)          |
| **F1-Score**   | Média harmônica entre precisão e recall (macro)                            |

As letras das alternativas (A, B, C, D) são convertidas para valores inteiros
antes do cálculo, e todas as métricas utilizam a estratégia `macro` para o
cálculo agregado.

## Resumo comparativo

| Aspecto              | `oab_bench` (Cruzada)                    | `oab_exams` (Exata)               |
|----------------------|------------------------------------------|------------------------------------|
| Tipo de resposta     | Discursiva (texto livre)                 | Objetiva (múltipla escolha)        |
| Referência           | Outros modelos + guidelines              | Gabarito oficial                   |
| Métricas             | BLEU, ROUGE, BERTScore                   | Acurácia, Precisão, Recall, F1     |
| Granularidade        | Por turno + média                        | Por modelo                         |
| Mínimo de modelos    | 2                                        | 1                                  |

## Onde os resultados são salvos

Os resultados da avaliação são salvos no diretório
`.reinan_cache/results/<dataset>/model_metric/` no formato JSON, com um arquivo
por modelo.
