---
marp: true
theme: marp-google-style
paginate: true
math: katex
---

<!-- _class: lead -->

## Curadoria de Datasets e Inferência Básica com LLMs

**Domínio Jurídico - Equipe 3**

**AUTOR**: Reinan Gabriel Dos Santos Souza

<!-- _footer: '06 de abril de 2026' -->

---

![bg left:40% 80%](https://www.qrtag.net/api/qr_1280.png?url=https://reinanhs.github.io/Topicos_Avancados_2026_1_Equipe_JUD_3_atividade1/docs)

**Material utilizado na apresentação**

Todos os materiais relacionados à apresentação estão disponíveis digitalmente no repositório do **GitHub**. Para acessar esses recursos, basta escanear o **QR Code** ao lado.

---

<!-- _header: Sumário -->

- Contexto e problema
- Objetivo
- Datasets utilizados
- Arquitetura do pipeline
- Modelos selecionados
- Métricas de avaliação
- Resultados
- Conclusão
- Trabalhos futuros

---

<!-- _header: CONTEXTO E PROBLEMA -->

1. **Avaliar LLMs compactos** no domínio jurídico brasileiro é desafiador;
2. **Questões da OAB** exigem raciocínio jurídico complexo;
3. **Questões abertas não possuem gabarito** oficial, dificultando a avaliação;
4. **Modelos com ≤ 3B parâmetros** têm recursos limitados para tarefas especializadas.

---

<!-- _header: OBJETIVO -->

Avaliar o desempenho de **três modelos de linguagem compactos** em tarefas do domínio jurídico brasileiro, utilizando dois datasets de questões da OAB.

| Dataset | Tipo | Quantidade |
|---|---|---|
| **J1 — OAB Bench** | Questões Abertas | 12 questões (lote 177–188) |
| **J2 — OAB Exams** | Múltipla Escolha | 122 questões (lote 1846–1968) |

> Fontes: `maritaca-ai/oab-bench` e `eduagarcia/oab_exams` no HuggingFace.

---

<!-- _header: ARQUITETURA DO PIPELINE -->

O projeto foi organizado em **4 etapas** principais:

1. **Curadoria**: classificação de dificuldade e identificação da legislação base
2. **Inferência**: execução dos modelos sobre os datasets
3. **Avaliação**: cálculo de métricas automáticas
4. **Análise**: interpretação dos resultados obtidos

A CLI centralizada expõe os comandos: `pull`, `run` e `evaluate`.

---

<!-- _header: ESTRUTURA DO PROJETO -->

```text
src/
├── dataset_manager.py    — Carregamento via HuggingFace
├── ollama_manager.py     — Integração com LLMs locais (Ollama)
├── execution_manager.py  — Orquestração do pipeline
├── evaluation_manager.py — Métricas (BLEU, ROUGE, BERTScore, F1)
└── storage_manager.py    — Persistência em JSON/CSV

prompts/                  — Templates .minijinja por tarefa
```

> Gerenciamento de dependências com `uv` e linting com `ruff`.

---

<!-- _header: MODELOS SELECIONADOS -->

Três modelos compactos executados localmente via **Ollama**:

| Modelo | Parâmetros |
|---|---|
| `gemma2:2b` | ~2 bilhões |
| `llama3.2:3b` | ~3 bilhões |
| `qwen2.5:3b` | ~3 bilhões |

```bash
uv run python main.py run oab_bench --model gemma2:2b
uv run python main.py run oab_exams --model gemma2:2b
```

---

<!-- _header: MÉTRICAS DE AVALIAÇÃO -->

**Questões abertas (J1)** — Avaliação cruzada entre modelos:

- **BLEU** — sobreposição de n-gramas
- **ROUGE** (1, 2, L) — cobertura de n-gramas
- **BERTScore F1** — similaridade semântica via embeddings

**Questões objetivas (J2)** — Avaliação exata contra gabarito:

- **Acurácia**, **Precisão**, **Recall**, **F1-Score**

---

<!-- _header: RESULTADOS — AVALIAÇÃO CRUZADA (OAB Bench) -->

Métricas de similaridade entre pares de modelos (12 questões abertas):

| Par de Modelos | BLEU | ROUGE-1 | ROUGE-L | BERTScore F1 |
|---|---|---|---|---|
| gemma2:2b vs llama3.2:3b | 0,1474 | 0,5094 | 0,2627 | 0,7665 |
| gemma2:2b vs qwen2.5:3b | 0,1413 | 0,5063 | 0,2440 | 0,7588 |
| llama3.2:3b vs qwen2.5:3b | **0,1515** | **0,5222** | **0,2620** | **0,7672** |

> Todos os pares com BERTScore F1 > 0,75 — boa concordância semântica apesar da baixa sobreposição lexical.

---

<!-- _header: RESULTADOS — AVALIAÇÃO EXATA (OAB Exams) -->

Desempenho dos modelos em 122 questões de múltipla escolha:

| Modelo | Acurácia | Precisão | Recall | F1 |
|---|---|---|---|---|
| **gemma2:2b** | **0,4508** | **0,4846** | **0,4532** | **0,4457** |
| qwen2.5:3b | 0,4016 | 0,4344 | 0,4064 | 0,4059 |
| llama3.2:3b | 0,3852 | 0,3896 | 0,3845 | 0,3781 |

> Nenhum modelo ultrapassou 50% — resultado esperado para modelos ≤ 3B em questões jurídicas complexas.

---

<!-- _header: PRINCIPAIS DESCOBERTAS -->

- O **gemma2:2b** foi o melhor modelo mesmo com menos parâmetros;
- O par **llama3.2 vs qwen2.5** gerou respostas mais similares entre si;
- **BERTScore** se mostrou mais adequado que BLEU para capturar similaridade semântica em textos jurídicos;
- A curadoria automatizada (dificuldade + legislação) via LLM funcionou como etapa complementar.

---

<!-- _header: CONCLUSÃO -->

- Pipeline reprodutível e modular para avaliação de LLMs no domínio jurídico.
- Modelos compactos (≤ 3B) ainda não atingem desempenho satisfatório na OAB.
- Métricas semânticas (BERTScore) complementam métricas lexicais (BLEU/ROUGE).
- Documentação completa publicada via Docs-as-Code com Docusaurus.

---

<!-- _header: TRABALHOS FUTUROS -->

- Testar modelos com mais parâmetros (7B, 13B) para comparação.
- Aplicar técnicas de **fine-tuning** no domínio jurídico.
- Incorporar **RAG** com legislação brasileira como contexto.
- Expandir a avaliação para outros exames jurídicos além da OAB.

---

<!-- _header: PRINCIPAIS REFERÊNCIAS -->

**Databricks (2024)**. Best Practices and Methods for LLM Evaluation. Disponível em: https://www.databricks.com/br/blog/best-practices-and-methods-llm-evaluation.
**Confident AI (2024)**. LLM Evaluation Metrics. Disponível em: https://www.confident-ai.com/blog/llm-evaluation-metrics-everything-you-need-for-llm-evaluation.
**Zhao, H. et al. (2025)**. LLM Evaluation: A Comprehensive Survey. arXiv. Disponível em: https://arxiv.org/html/2504.21202v1.

---

<!-- _class: lead -->

## Obrigado!

**Reinan Gabriel Dos Santos Souza**

Repositório: https://github.com/reinanhs/Topicos_Avancados_2026_1_Equipe_JUD_3_atividade1
Vídeo: https://youtu.be/lcOxhH8N3Bo