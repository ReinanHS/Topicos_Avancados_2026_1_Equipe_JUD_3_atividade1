---
sidebar_position: 4
---

# Estrutura do projeto

Esta página apresenta a organização geral do repositório e resume a
responsabilidade de cada arquivo e diretório. O objetivo é facilitar a navegação
no código e indicar onde estão os componentes principais da aplicação.

## Visão geral da estrutura

```text
.
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── Makefile
├── README-EN.md
├── README.md
├── SECURITY.md
├── VERSION
├── docs
├── main.py
├── prompts
│   ├── curador
│   │   ├── area_expertise
│   │   │   ├── system_template.minijinja
│   │   │   └── user_template.minijinja
│   │   ├── basic_legislation
│   │   │   ├── system_template.minijinja
│   │   │   └── user_template.minijinja
│   │   └── classify_difficulty
│   │       ├── system_template.minijinja
│   │       └── user_template.minijinja
│   ├── judge
│   │   ├── multi-turn
│   │   │   ├── system_template.minijinja
│   │   │   └── user_template.minijinja
│   │   └── single-turn
│   │       ├── system_template.minijinja
│   │       └── user_template.minijinja
│   ├── oab_bench
│   │   ├── system_template.minijinja
│   │   └── user_template.minijinja
│   └── oab_exams
│       ├── system_template.minijinja
│       └── user_template.minijinja
├── pyproject.toml
├── sonar-project.properties
├── src
│   ├── __init__.py
│   ├── cli
│   │   ├── __init__.py
│   │   │   ├── __init__.py
│   │   │   └── app.py
│   │   └── app.py
│   ├── datasets
│   │   ├── __init__.py
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── loader_factory.py
│   │   │   ├── oab_bench_loader.py
│   │   │   └── oab_exams_loader.py
│   │   ├── base.py
│   │   ├── loader_factory.py
│   │   ├── oab_bench_loader.py
│   │   └── oab_exams_loader.py
│   ├── evaluation
│   │   ├── __init__.py
│   │   │   ├── __init__.py
│   │   │   ├── cross_model_evaluator.py
│   │   │   └── exact_match_evaluator.py
│   │   ├── cross_model_evaluator.py
│   │   └── exact_match_evaluator.py
│   ├── execution
│   │   ├── __init__.py
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── executor_factory.py
│   │   │   ├── oab_bench_executor.py
│   │   │   └── oab_exams_executor.py
│   │   ├── base.py
│   │   ├── executor_factory.py
│   │   ├── oab_bench_executor.py
│   │   └── oab_exams_executor.py
│   ├── judgment
│   │   ├── __init__.py
│   │   │   ├── __init__.py
│   │   │   └── judge_manager.py
│   │   └── judge_manager.py
│   ├── llm
│   │   ├── __init__.py
│   │   │   ├── __init__.py
│   │   │   ├── base_client.py
│   │   │   ├── ollama_client.py
│   │   │   └── openai_client.py
│   │   ├── base_client.py
│   │   ├── ollama_client.py
│   │   └── openai_client.py
│   ├── prompts
│   │   ├── __init__.py
│   │   │   ├── __init__.py
│   │   │   └── renderer.py
│   │   └── renderer.py
│   ├── publishing
│   │   ├── __init__.py
│   │   │   ├── __init__.py
│   │   │   ├── publisher.py
│   │   │   └── readme_generator.py
│   │   ├── publisher.py
│   │   ├── readme_generator.py
│   │   └── templates
│   │       └── readme.md.jinja
│   ├── reporting
│   │   ├── __init__.py
│   │   │   ├── __init__.py
│   │   │   ├── base_chart_generator.py
│   │   │   ├── chart_generator.py
│   │   │   ├── chart_generator_factory.py
│   │   │   ├── oab_bench_chart_generator.py
│   │   │   └── oab_exams_chart_generator.py
│   │   ├── base_chart_generator.py
│   │   ├── chart_generator_factory.py
│   │   ├── oab_bench_chart_generator.py
│   │   └── oab_exams_chart_generator.py
│   └── storage
│       ├── __init__.py
│       ├── __pycache__
│       │   ├── __init__.py
│       │   ├── csv_serializer.py
│       │   ├── file_serializer.py
│       │   ├── json_serializer.py
│       │   └── local_storage.py
│       ├── csv_serializer.py
│       ├── file_serializer.py
│       ├── json_serializer.py
│       └── local_storage.py
└── uv.lock
````

## Arquivos da raiz do projeto

### `CHANGELOG.md`

Registra as principais mudanças realizadas no projeto ao longo do tempo. Este
arquivo é útil para acompanhar correções, melhorias e novas funcionalidades.

### `CONTRIBUTING.md`

Descreve orientações para contribuir com o projeto. Pode incluir regras de
organização, padrões de código, fluxo de trabalho e boas práticas para novas
alterações.

### `LICENSE`

Define a licença de uso do repositório. Esse arquivo informa como o código pode
ser utilizado, modificado e redistribuído.

### `Makefile`

Centraliza comandos de automação usados no desenvolvimento. Em geral, esse
arquivo facilita tarefas repetitivas, como executar scripts, validar arquivos ou
gerar artefatos.

### `README.md`

Apresenta a visão geral do repositório. Normalmente é o primeiro arquivo lido
por quem acessa o projeto e deve explicar o propósito da aplicação, como
executá-la e onde encontrar a documentação complementar.

### `main.py`

É o ponto de entrada da aplicação em linha de comando. Esse arquivo recebe os
comandos executados pelo usuário, como `pull`, `run` e `evaluate`, e aciona os
componentes internos responsáveis por cada etapa do pipeline.

### `pyproject.toml`

Define os metadados do projeto Python, as dependências e possíveis configurações
de ferramentas do ecossistema. É um dos arquivos centrais para instalação e
gerenciamento do ambiente.

### `uv.lock`

Armazena o travamento exato das versões das dependências instaladas com o `uv`.
Isso ajuda a reproduzir o ambiente com mais consistência em outras máquinas.

## Diretório `docs`

O diretório `docs` reúne arquivos relacionados à documentação escrita e aos
artefatos acadêmicos do projeto.

### `docs/activity_description.pdf`

Contém o enunciado ou a descrição formal da atividade. Esse arquivo serve como
referência para compreender os objetivos, regras e entregáveis definidos para o
trabalho.

### `docs/pdf/main.tex`

Arquivo principal em LaTeX utilizado para gerar a versão em PDF da documentação
ou do relatório da atividade.

## Diretório `prompts`

O diretório `prompts` reúne os templates utilizados para montar as instruções
enviadas aos modelos de linguagem. Esses arquivos são importantes porque
separam o conteúdo dos prompts da lógica do código.

## Diretório `src`

O diretório `src` concentra o código-fonte principal da aplicação.

### `src/__init__.py`

Indica que o diretório `src` deve ser tratado como um pacote Python.

### `src/dataset_manager.py`

Responsável pelo gerenciamento dos datasets. Esse módulo tende a concentrar
rotinas de carregamento, filtragem, preparação e organização dos dados usados
na atividade.

### `src/evaluation_manager.py`

Implementa a lógica de avaliação dos resultados gerados pelos modelos. É nesse
tipo de módulo que normalmente ficam o cálculo de métricas e a comparação entre
respostas e referências.

### `src/execution_manager.py`

Coordena o fluxo principal de execução do projeto. Esse arquivo costuma atuar na
orquestração entre dataset, prompts, modelo e armazenamento dos resultados.

### `src/ollama_manager.py`

Centraliza a integração com o Ollama. Esse módulo é responsável por preparar e
executar chamadas aos modelos locais utilizados no projeto.

### `src/storage_manager.py`

Gerencia a persistência dos dados produzidos pela aplicação. Isso pode incluir o
salvamento de datasets processados, respostas geradas e resultados de avaliação.
