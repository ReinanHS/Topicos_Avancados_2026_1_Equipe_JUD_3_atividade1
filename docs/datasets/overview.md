---
sidebar_position: 1
---

# Visão geral dos datasets

O projeto utiliza dois datasets do domínio jurídico brasileiro, ambos
relacionados ao Exame da Ordem dos Advogados do Brasil (OAB). Esses conjuntos de
dados foram usados nas etapas de curadoria, inferência e avaliação realizadas ao
longo da atividade.

## Datasets utilizados

| Dataset   | Identificador           | Tipo          | Questões                                    |
|-----------|-------------------------|---------------|---------------------------------------------|
| OAB Bench | `maritaca-ai/oab-bench` | Dissertativas | Questões abertas com resposta de referência |
| OAB Exams | `eduagarcia/oab_exams`  | Objetivas     | Questões de múltipla escolha                |

## Por que o domínio jurídico?

O domínio jurídico não foi escolhido livremente por cada integrante. A definição
das equipes que trabalhariam com o domínio jurídico e com o domínio médico foi
feita pelo professor responsável pela disciplina.

Embora parte da equipe já demonstrasse interesse pelo domínio jurídico, a
distribuição final dos temas ocorreu por sorteio. Como resultado, a Equipe 3 foi
alocada para trabalhar com datasets jurídicos relacionados ao exame da OAB.

## Fonte dos dados

Os dois datasets estão disponíveis publicamente no Hugging Face. Eles foram
adotados na atividade por representarem bases adequadas para experimentos com
LLMs em português brasileiro no contexto jurídico.

## Papel dos datasets no projeto

Cada dataset atende a uma finalidade diferente dentro do pipeline:

- **OAB Bench**: utilizado principalmente para inferência em questões abertas e
  comparação entre respostas geradas pelos modelos
- **OAB Exams**: utilizado para inferência em questões objetivas com comparação
  baseada no gabarito da questão

Essa separação permite avaliar os modelos em dois cenários distintos:
interpretação e argumentação em questões dissertativas, e seleção de resposta em
questões de múltipla escolha.
