---
sidebar_position: 2
---

# Classificação de dificuldade

Esta página descreve os critérios utilizados para classificar cada questão em um
dos três níveis de dificuldade adotados na curadoria.

## Critérios adotados

A classificação de dificuldade foi baseada no **tipo de operação cognitiva**
exigida pela questão, e não no tamanho do enunciado ou na quantidade de
alternativas. Essa abordagem é inspirada em taxonomias cognitivas aplicadas ao
domínio jurídico, priorizando a complexidade do raciocínio necessário para se
chegar à resposta correta.

## Níveis de dificuldade

| Nível | Valor | Nome técnico                                   | Critérios de identificação                                                                                                                                                                                     |
|-------|-------|------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Fácil | 1     | Recuperação Factual Direta (*Fact Retrieval*)   | A resposta depende apenas da memorização de um artigo de lei específico ou conceito exato. O modelo só precisa "lembrar" a informação, sem necessidade de raciocínio adicional.                                 |
| Médio | 2     | Raciocínio Lógico-Dedutivo (*Logical Deduction*) | A questão apresenta um caso concreto. O modelo precisa extrair os fatos do enunciado e aplicar uma regra jurídica clara (Se A, então B).                                                                       |
| Difícil | 3   | Hermenêutica Jurídica Complexa (*Complex Hermeneutics*) | A questão exige interpretação profunda, cruzamento de múltiplas leis, análise de jurisprudência ou lida com ambiguidades legais.                                                                               |

## Regras de classificação

As regras abaixo orientam o classificador (LLM curador) na análise:

1. O enunciado completo deve ser avaliado, incluindo subitens e alternativas,
   antes de classificar.
2. O critério principal é o **tipo de operação cognitiva** exigida, não a
   extensão do texto.
3. Questões com peças prático-profissionais são sempre **Nível 3**.
4. Se a questão pede apenas a literalidade de um dispositivo legal, é **Nível
   1**, mesmo que o enunciado seja longo.
5. Se há um caso concreto mas a subsunção é direta (uma única regra aplicável
   sem ambiguidade), é **Nível 2**.

## Como a classificação foi realizada

A classificação foi realizada de forma automatizada por meio de um LLM curador
(por padrão `gpt-4o-mini`), responsável por ler a questão, avaliar a operação
cognitiva predominante e indicar o nível de dificuldade com base nos critérios
definidos.

Essa abordagem permitiu aplicar o mesmo padrão de análise a todas as questões,
reduzindo variações manuais no processo de curadoria.

- [Clique neste link para visualizar um exemplo de prompt](/resultados/prompts)

## Exemplo de saída

O exemplo abaixo mostra uma saída gerada no processo de classificação:

```json
{
  "difficulty_question": 2
}
```

O campo `difficulty_question` aceita os valores `1`, `2` ou `3`, correspondendo
aos níveis Fácil, Médio e Difícil, respectivamente.
