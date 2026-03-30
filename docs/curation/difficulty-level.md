---
sidebar_position: 2
---

# Classificação de dificuldade

Esta página descreve os critérios utilizados para classificar cada questão em um
dos três níveis de dificuldade adotados na curadoria.

## Critérios adotados

A classificação de dificuldade foi baseada em critérios inspirados nas
orientações divulgadas pelo
[Estratégia OAB](https://oab.estrategia.com/portal/como-identificar-questoes-faceis-medias-e-dificeis-na-1a-fase-da-oab/),
considerando também padrões recorrentes em provas elaboradas pela FGV.

Esses critérios foram usados como referência para apoiar a análise das questões
e permitir uma classificação mais consistente durante a curadoria.

## Níveis de dificuldade

| Nível | Valor | Critérios de identificação |
|---|---|---|
| Fácil | 1 | Enunciado curto, linguagem direta e aplicação imediata de um conceito jurídico básico. O comando da questão pode ser identificado com rapidez e não exige interpretação complexa. |
| Médio | 2 | Enunciado com tamanho intermediário, presença mais frequente de termos técnicos e necessidade de leitura cuidadosa. Exige raciocínio jurídico, mas sem elevado grau de complexidade conceitual. |
| Difícil | 3 | Enunciado mais longo, com situação hipotética detalhada, necessidade de interpretação mais aprofundada da legislação ou de princípios jurídicos, além de maior proximidade entre alternativas ou combinação de múltiplos temas jurídicos. |

## Como a classificação foi realizada

A classificação pode ser feita manualmente ou com apoio automatizado. Nesta
implementação, o processo foi realizado por meio de um LLM curador, responsável
por ler a questão e indicar o nível de dificuldade com base nos critérios
definidos.

Essa abordagem permitiu aplicar o mesmo padrão de análise a diferentes questões,
reduzindo variações manuais no processo de curadoria.

- [Clique neste link para visualizar um exemplo de prompt](/resultados/prompts)

## Exemplo de saída

O exemplo abaixo mostra uma saída gerada no processo de classificação:

```json
{
  "question_id": "41_direito_administrativo_questao_1",
  "dificuldade": 2,
  "nivel": "Médio"
}
```
