---
sidebar_position: 1
---

# Visão geral da inferência

O pipeline de inferência é responsável por enviar cada questão do dataset para
os LLMs locais (via Ollama) e coletar as respostas geradas. Além da resposta
principal, o pipeline também executa automaticamente tarefas de curadoria em cada
questão processada.

## Como funciona

O comando `infer` orquestra o fluxo completo de inferência. Para cada questão, o
sistema executa **quatro operações** de forma sequencial:

1. **Resposta à questão**: o LLM recebe o prompt com a questão e gera a
   resposta (discursiva ou objetiva, conforme o dataset).
2. **Classificação de dificuldade**: o mesmo modelo classifica o nível de
   dificuldade cognitiva da questão (1, 2 ou 3).
3. **Identificação da legislação base**: o modelo identifica a principal
   referência normativa relacionada à questão.
4. **Identificação da área de expertise**: o modelo identifica a área do
   direito associada à questão.

Essas quatro etapas são encapsuladas no método `process_full_question` da classe
`ExecutionManager`.

## Modelos utilizados

A inferência é executada localmente via [Ollama](https://ollama.ai/) utilizando
os seguintes modelos:

| Modelo        | Parâmetros | Finalidade           |
|---------------|------------|----------------------|
| `llama3.2:3b` | 3B         | Inferência principal |
| `gemma2:2b`   | 2B         | Inferência principal |
| `qwen2.5:3b`  | 3B         | Inferência principal |

Quando o comando `infer` é executado sem a flag `--model`, todos os três modelos
são processados automaticamente. Entre cada modelo, o sistema aguarda **15
segundos** para permitir a limpeza de VRAM e estabilização do serviço Ollama.

## Estratégias de inferência por dataset

O sistema adota estratégias de inferência diferentes para cada dataset, implementadas por executores especializados.

### `oab_bench`: Multi-turn

O dataset `oab_bench` contém questões discursivas da segunda fase da OAB,
geralmente com múltiplos subitens (turnos). A estratégia utilizada é
**multi-turn**: o LLM recebe o contexto fático uma única vez e responde a cada
subitem em sequência, mantendo o histórico completo de mensagens entre as
chamadas.

O fluxo para cada questão funciona da seguinte forma:

1. O prompt de sistema é carregado a partir do template `oab_bench/system_template.minijinja`
   (que geralmente utiliza o campo `system` do próprio dataset).
2. Para o primeiro turno, o modelo recebe o contexto fático (`statement`) e o
   primeiro subitem.
3. Para os turnos seguintes, o histórico acumulado é mantido e o novo subitem é
   adicionado como mensagem do usuário.
4. Ao final, todas as respostas dos turnos são consolidadas em uma lista de
   `choices`.

**API utilizada:** `generate_chat_response` (multi-turn com histórico de mensagens)

### `oab_exams`: Single-turn

O dataset `oab_exams` contém questões objetivas de múltipla escolha da primeira
fase da OAB. A estratégia utilizada é **single-turn**: cada questão é enviada em
uma única chamada ao LLM, que retorna a resposta como um JSON com a letra da
alternativa escolhida.

O fluxo para cada questão funciona da seguinte forma:

1. O prompt de sistema é carregado a partir do template `oab_exams/system_template.minijinja`,
   que instrui o modelo a retornar exclusivamente um JSON com o campo
   `resposta_objetiva`.
2. O prompt de usuário é renderizado com o enunciado da questão e as
   alternativas formatadas.
3. A resposta JSON é parseada para extrair a letra da alternativa escolhida.

**API utilizada:** `generate_response` (single-turn)

## Estrutura de saída

Para cada questão processada, o sistema gera um registro com a seguinte
estrutura:

```json
{
  "question_id": "41_direito_constitucional_questao_1",
  "answer_id": "a1b2c3d4e5f6...",
  "model_id": "llama3.2:3b",
  "choices": [ ... ],
  "additional_information": {
    "difficulty_question": 2,
    "basic_legislation": "Constituição Federal, Art. 5º",
    "area_expertise": "Direito Constitucional"
  },
  "tstamp": 1712612345.678
}
```

| Campo                    | Descrição                                              |
|--------------------------|--------------------------------------------------------|
| `question_id`            | Identificador único da questão no dataset              |
| `answer_id`              | UUID gerado automaticamente para cada resposta         |
| `model_id`               | Nome do modelo que gerou a resposta                    |
| `choices`                | Respostas geradas (formato varia por dataset)          |
| `additional_information` | Metadados de curadoria (dificuldade, legislação, área) |
| `tstamp`                 | Timestamp Unix do momento da geração                   |

Os resultados são salvos em `.reinan_cache/results/<dataset>/model_answer/` no
formato JSON, com um arquivo por modelo (ex: `llama3-2-3b.json`).

## Mecanismo de retry

O `OllamaClient` implementa um mecanismo de retry automático com até **3
tentativas** por chamada. Se o Ollama falhar (ex: timeout de 300 segundos ou
travamento de VRAM), o sistema aguarda 5 segundos antes de cada retentativa.
Caso todas as tentativas falhem, uma mensagem de erro é exibida com orientações
para reiniciar o serviço do Ollama.