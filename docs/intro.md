---
sidebar_position: 1
slug: /
---

# Visão geral do projeto

Esta documentação apresenta as contribuições individuais de [**Reinan Souza**](https://github.com/reinanhs) na **Atividade Avaliativa 1** da disciplina de **Tópicos Avançados em Engenharia de Software e Sistemas de Informação I**. O projeto foi desenvolvido no domínio jurídico pela **Equipe 3** e tem como foco a curadoria de datasets e a inferência básica com **LLMs locais** para responder questões do exame da OAB.

Embora a entrega final da atividade seja feita em equipe, parte relevante da execução é individual. Por isso, esta documentação destaca principalmente as tarefas implementadas por Reinan, sem deixar de registrar decisões e definições que foram discutidas coletivamente pelo grupo.

## Objetivo

O objetivo do projeto é avaliar o desempenho de modelos de linguagem compactos
em tarefas do domínio jurídico brasileiro, utilizando dois datasets principais:

- [**OAB Bench**](https://huggingface.co/datasets/maritaca-ai/oab-bench): conjunto de questões dissertativas sem gabarito objetivo,
  usado para comparação entre respostas geradas por diferentes modelos
- [**OAB Exams**](https://huggingface.co/datasets/eduagarcia/oab_exams): conjunto de questões objetivas de provas reais da OAB,
  usado para avaliação com base no gabarito

## Escopo desta documentação

Esta documentação tem como foco apresentar as contribuições desenvolvidas individualmente. Embora o trabalho tenha sido realizado em equipe, a primeira avaliação foi dividida entre etapas individuais e etapas coletivas. As atividades em grupo envolveram principalmente discussões sobre métricas e critérios de curadoria. Já a implementação do código e a coleta das respostas foram realizadas individualmente. Por isso, esta documentação busca registrar o processo conduzido pelo aluno Reinan Souza em sua parte da atividade.

As contribuições individuais de Reinan incluem:

- curadoria de questões jurídicas
- execução de inferência com LLMs locais
- avaliação automática dos resultados
- organização da documentação técnica do projeto

No recorte definido para a atividade, Reinan ficou responsável pelos seguintes
intervalos:

- **Questões abertas**: 177 a 188
- **Questões objetivas**: 1846 a 1968

## Fluxo do projeto

O projeto foi organizado em um pipeline com quatro etapas principais:

1. **Curadoria**: classificação do nível de dificuldade e identificação da
   legislação base das questões
2. **Inferência**: execução dos modelos selecionados sobre os datasets
3. **Avaliação**: cálculo de métricas automáticas para comparar os resultados
4. **Análise**: interpretação dos resultados obtidos por cada modelo

## Tecnologias utilizadas

| Tecnologia | Uso no projeto |
|---|---|
| Python + UV | Backend, CLI e gerenciamento de dependências |
| Ollama | Execução local dos modelos de linguagem |
| MiniJinja | Renderização de templates de prompt |
| Docusaurus | Documentação e visualização dos resultados |
| evaluate / bert-score | Cálculo de métricas de avaliação |

## Sobre a equipe

A atividade foi desenvolvida por seis integrantes da Equipe 3. No entanto,
esta documentação não pretende substituir o material consolidado da equipe.
Seu propósito é registrar, de forma objetiva, as contribuições implementadas
individualmente por Reinan no repositório sob sua responsabilidade.

## Links rápidos

- [Guia rápido](./getting-started/quick-start)
- [Datasets](./datasets/overview)
- [Resultados](./results/overview)
