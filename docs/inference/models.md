---
sidebar_position: 2
---

# Modelos

## Modelos selecionados

Os experimentos utilizaram os seguintes modelos:

| # | Modelo           | Desenvolvedor | Comando Ollama           |
|---|------------------|---------------|--------------------------|
| 1 | **Llama 3.2 3B** | Meta          | `ollama run llama3.2:3b` |
| 2 | **Gemma 2 2B**   | Google        | `ollama run gemma2:2b`   |
| 3 | **Qwen 2.5 3B**  | Alibaba       | `ollama run qwen2.5:3b`  |

## Critérios de seleção

Os modelos foram selecionados com base nos critérios abaixo.

### Diversidade de origem

Os três modelos foram desenvolvidos por organizações diferentes: Meta, Google e
Alibaba. Isso permite comparar abordagens distintas no mesmo conjunto de
questões jurídicas.

### Suporte ao idioma português

Os três modelos oferecem suporte ao português, o que é necessário para a
inferência em questões do Exame da OAB, escritas em português brasileiro.

### Compatibilidade com Ollama

Todos os modelos estão disponíveis no Ollama. Isso garante:

- execução local padronizada
- a mesma interface de uso para todos os modelos
- maior facilidade de reprodução dos experimentos

## Modelo juiz

Além da inferência, o modelo **Llama 3.2 3B** (`llama3.2:3b`) foi utilizado como
modelo juiz nas seguintes tarefas:

- avaliação por rubrica de questões abertas
- comparação entre respostas geradas pelos modelos
- apoio às tarefas de curadoria, como classificação de dificuldade e
  identificação da legislação de referência

O **Llama 3.2 3B** foi escolhido para esse papel por apresentar bom desempenho
em tarefas de compreensão e avaliação de textos em português.

## Instalação

Use os comandos abaixo para baixar os modelos:

```bash
ollama pull llama3.2:3b
ollama pull gemma2:2b
ollama pull qwen2.5:3b
```
