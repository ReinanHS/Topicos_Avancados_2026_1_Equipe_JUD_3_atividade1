---
sidebar_position: 3
---

# OAB Exams

O **OAB Exams** é o dataset utilizado no projeto para trabalhar com questões
objetivas do Exame da Ordem dos Advogados do Brasil. Ele reúne perguntas de
múltipla escolha com alternativas e gabarito, o que permite avaliar com mais
objetividade o desempenho dos modelos.

## Origem

O dataset `eduagarcia/oab_exams` reúne provas da OAB aplicadas no Brasil entre
2010 e 2018. Ele foi disponibilizado publicamente no Hugging Face e organiza as
questões em um formato adequado para experimentos com modelos de linguagem e
sistemas de avaliação automática.

Por conter questões objetivas com resposta correta definida, esse dataset é
especialmente útil em cenários de inferência nos quais a saída do modelo pode
ser comparada diretamente com o gabarito oficial.

Para uma visualização mais detalhada do dataset no projeto, acesse a página
abaixo:

- [Visualização detalhada](/resultados/datasets)

## Estrutura dos campos

A tabela abaixo resume os principais campos usados no dataset:

| Campo             | Tipo             | Descrição                                                 |
|-------------------|------------------|-----------------------------------------------------------|
| `id`              | `string`         | Identificador único da questão                            |
| `question_number` | `integer`        | Número da questão dentro da prova                         |
| `exam_id`         | `string`         | Identificador da edição do exame                          |
| `exam_year`       | `string`         | Ano de realização da prova                                |
| `question_type`   | `string \| null` | Classificação temática da questão, quando disponível      |
| `nullified`       | `boolean`        | Indica se a questão foi anulada                           |
| `question`        | `string`         | Enunciado principal da questão                            |
| `choices`         | `object`         | Conjunto de alternativas da questão, com textos e rótulos |
| `answerKey`       | `string`         | Alternativa correta segundo o gabarito oficial            |

## Como o dataset foi usado no projeto

No contexto desta atividade, o OAB Exams foi utilizado na execução de
inferências sobre questões de múltipla escolha. Como cada item possui uma
alternativa correta, esse dataset foi usado na etapa de avaliação exata das
respostas, permitindo comparar diretamente a saída do modelo com o gabarito da
questão.

## Exemplo

O exemplo abaixo mostra uma questão do dataset com seus campos principais:

```json
{
  "id": "2016-21_36",
  "question_number": 36,
  "exam_id": "2016-21",
  "exam_year": "2016",
  "question_type": null,
  "nullified": false,
  "question": "O Governo Federal, tendo em vista a grande dificuldade em conter o desmatamento irregular em florestas públicas, iniciou procedimento de concessão florestal para que particulares possam explorar produtos e serviços florestais.\nSobre o caso, assinale a afirmativa correta.",
  "choices": {
    "text": [
      "Essa concessão é antijurídica, uma vez que o dever de tutela do meio ambiente ecologicamente equilibrado é intransferível a inalienável.",
      "Essa concessão, que tem como objeto o manejo florestal sustentável, deve ser precedida de licitação na modalidade de concorrência.",
      "Essa concessão somente é possível para fins de exploração de recursos minerais pelo concessionário.",
      "Essa concessão somente incide sobre florestas públicas estaduais e, por isso, a competência para sua delegação é exclusiva dos Estados, o que torna ilegal sua implementação pelo IBAMA."
    ],
    "label": [
      "A",
      "B",
      "C",
      "D"
    ]
  },
  "answerKey": "B"
}
```
