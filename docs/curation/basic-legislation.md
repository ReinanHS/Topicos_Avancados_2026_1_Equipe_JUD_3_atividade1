---
sidebar_position: 3
---

# Legislação base

Esta página descreve a etapa de identificação da principal referência normativa
associada a cada questão do dataset.

## Objetivo

O objetivo dessa etapa é enriquecer o dataset com a informação sobre qual
legislação serve como base principal para a resolução de cada questão, como
Constituição Federal, Código Civil, Código Penal ou outras normas relevantes do
domínio jurídico.

Esse tipo de anotação adiciona contexto às questões e facilita análises
posteriores durante a curadoria e a interpretação dos resultados.

## Como funciona

A identificação da legislação base é realizada automaticamente com apoio de um
LLM. Durante esse processo, o modelo analisa o enunciado da questão e indica a
principal referência normativa relacionada ao problema apresentado.

Nesta implementação, essa tarefa foi integrada ao fluxo automatizado de
curadoria, permitindo aplicar o mesmo procedimento a diferentes questões de
forma consistente e reprodutível.

Abaixo está o link para um exemplo do prompt utilizado nessa classificação:

- [Clique neste link para visualizar um exemplo de prompt](/resultados/prompts)

## Exemplo de saída

O exemplo abaixo mostra uma saída gerada no processo de identificação da
legislação base:

```json
{
  "question_id": "41_direito_administrativo_questao_1",
  "legislacao_base": "Constituição Federal, art. 71, III"
}
```
