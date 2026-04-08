---
sidebar_position: 1
---

# Visão geral da curadoria

A curadoria é a etapa em que as questões dos datasets recebem informações
adicionais que ajudam a organizar, interpretar e reutilizar os dados ao longo do
projeto. Nesta atividade, essa etapa foi aplicada ao subconjunto de questões sob
responsabilidade individual de Reinan Souza.

No contexto desta documentação, a curadoria foi tratada como um processo de
enriquecimento dos dados com metadados jurídicos gerados de forma automatizada,
utilizando modelos de linguagem executados localmente.

## O que é curadoria neste contexto?

Na atividade acadêmica, cada aluno atua como curador de um subconjunto
específico de questões. Esse papel envolve analisar os itens atribuídos e
registrar informações que complementam o conteúdo original do dataset.

Essas informações não substituem o enunciado da questão, mas acrescentam uma
camada de organização útil para etapas posteriores, como inferência, análise e
avaliação. Na prática, a curadoria ajuda a transformar o dataset em um conjunto
mais estruturado para experimentação com LLMs.

Embora a atividade inclua discussões coletivas sobre critérios e categorias, a
execução da curadoria sobre cada lote de questões foi realizada individualmente.

## Tarefas de curadoria

Nesta implementação, a curadoria concentrou-se em duas tarefas principais:

1. **Classificação de dificuldade**: cada questão é classificada em um nível de
   dificuldade
2. **Identificação de legislação base**: a principal referência normativa
   relacionada à questão é identificada
3. **Identificação de área de expertise**: a área de expertise relacionada à questão é identificada

Essas três informações foram utilizadas como metadados adicionais para apoiar a
organização e a interpretação das questões do domínio jurídico.

## Abordagem utilizada

A curadoria foi implementada de forma automatizada e reprodutível, com o uso de
prompts estruturados enviados a modelos locais por meio do Ollama.

Essa abordagem foi adotada para reduzir a execução manual repetitiva e manter um
fluxo consistente entre diferentes execuções. Com a mesma configuração de
ambiente, os mesmos prompts e os mesmos modelos, o processo pode ser repetido em
outras máquinas.

## Resultado da curadoria

Ao final dessa etapa, cada questão processada passa a contar com informações
adicionais que não estavam presentes originalmente no dataset bruto. Esses
metadados enriquecem o conjunto de dados e servem de apoio tanto para análise
quanto para documentação dos resultados obtidos ao longo da atividade.
