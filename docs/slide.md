---
marp: true
theme: marp-google-style
paginate: true
math: katex
---

<!-- _class: lead -->

# Atividade 01

## Curadoria de Datasets e Inferência Básica com LLMs

**Domínio Jurídico: Equipe 3**

Tópicos Avançados em Engenharia de Software e Sistemas de Informação I
Mestrado em Ciências da Computação — Procc/UFS

<!-- _footer: 'Abril de 2026' -->

---

<!-- _header: INTEGRANTES DA EQUIPE -->

| Membro          | Questões abertas | Múltipla escolha |
|-----------------|------------------|------------------|
| Fernanda Mirely | 141 a 152        | 1477 a 1599      |
| Éricles         | 153 a 164        | 1600 a 1722      |
| Júlia           | 165 a 176        | 1723 a 1845      |
| Reinan Gabriel  | 177 a 188        | 1846 a 1968      |
| Mikaela         | 189 a 200        | 1969 a 2091      |
| Victor Leonardo | 201 a 210        | 2092 a 2210      |

---

<!-- _header: DATASETS UTILIZADOS -->

| Dataset            | Identificador           | Tipo             | Total          |
|--------------------|-------------------------|------------------|----------------|
| **OAB Bench** | `maritaca-ai/oab-bench` | Questões Abertas | 210 questões   |
| **OAB Exams** | `eduagarcia/oab_exams`  | Múltipla Escolha | 2.210 questões |

- **OAB Bench**: Questões dissertativas da **2ª fase** da OAB, com enunciado, subitens e
  guidelines de correção (benchmark da Maritaca AI)
- **OAB Exams**: Questões objetivas da **1ª fase** da OAB (provas de 2010 a 2018), com
  4 alternativas e gabarito oficial (dataset de Eduardo Garcia)

---

<!-- _header: METODOLOGIA: VISÃO GERAL -->

O trabalho foi dividido em **4 etapas** executadas individualmente:

1. **Curadoria e classificação criativa**
   - Nível de dificuldade (3 níveis cognitivos)
   - Área de especialidade jurídica
   - Legislação base de referência

2. **Inferência com LLMs**
   - Cada membro selecionou **3 modelos** de linguagem
   - Submissão das questões abertas e objetivas aos modelos

3. **Avaliação automática**
   - Métricas automáticas para comparar as respostas geradas

---

<!-- _header: CURADORIA: CLASSIFICAÇÃO DE DIFICULDADE -->

A classificação foi baseada no **tipo de operação cognitiva** exigida pela questão, não no tamanho do enunciado.

| Nível | Nome técnico                   | Critérios                                      |
|-------|--------------------------------|------------------------------------------------|
| **1** | Recuperação factual direta     | Memorização de artigo de lei ou conceito exato |
| **2** | Raciocínio lógico-dedutivo     | Caso concreto + aplicação de regra clara       |
| **3** | Hermenêutica jurídica complexa | Interpretação profunda, cruzamento de leis     |

---

<!-- _header: CURADORIA: LEGISLAÇÃO BASE E ÁREA DE EXPERTISE -->

### Legislação base
Identifica a **principal referência normativa** associada à questão:
- Ex: *Constituição Federal, Art. 5º*, *Código Penal, Art. 121*, *Lei nº 14.133/2021*

### Área de expertise
Identifica a **área do direito** relacionada à questão:
- Ex: *Direito Constitucional*, *Direito Administrativo*, *Direito Penal*

### Exemplo de saída da curadoria

```json
{
  "difficulty_question": 2,
  "basic_legislation": "Constituição Federal, Art. 71, III",
  "area_expertise": "Direito Administrativo"
}
```

---

<!-- _header: CURADORIA: ABORDAGEM AUTOMATIZADA -->

A curadoria foi realizada de forma **automatizada e reprodutível**:

- Prompts estruturados definem o formato de saída esperado (JSON)
- Mesma configuração aplicada a **todos os integrantes**

| # | Operação                      | Saída                                |
|---|-------------------------------|--------------------------------------|
| 1 | Resposta à questão            | Texto discursivo ou letra (A–D)      |
| 2 | Classificação de dificuldade  | Valor 1, 2 ou 3                      |
| 3 | Identificação de legislação   | Referência normativa principal       |
| 4 | Identificação da área         | Área de expertise jurídica           |

---

<!-- _header: INFERÊNCIA: MODELOS UTILIZADOS -->

Cada integrante selecionou **3 modelos** compactos.

---

<!-- _header: MÉTRICAS DE AVALIAÇÃO: QUESTÕES ABERTAS (J1) -->

**OAB Bench**: sem gabarito oficial → avaliação **cruzada** entre modelos

Duas estratégias complementares:
1. **Modelo vs Modelo**: compara respostas entre cada par de modelos
2. **Modelo vs Guideline**: compara respostas contra as guidelines do dataset

| Métrica          | O que mede                                        | Escala |
|------------------|---------------------------------------------------|--------|
| **BLEU**         | Sobreposição de n-gramas (precisão lexical)       | 0 a 1  |
| **ROUGE-1**      | Sobreposição de unigramas (cobertura vocabular)   | 0 a 1  |
| **ROUGE-2**      | Sobreposição de bigramas (estrutura local)        | 0 a 1  |
| **ROUGE-L**      | Maior subsequência comum (estrutura global)       | 0 a 1  |
| **BERTScore F1** | Similaridade semântica via embeddings contextuais | 0 a 1  |

---

<!-- _header: MÉTRICAS DE AVALIAÇÃO: QUESTÕES OBJETIVAS (J2) -->

**OAB Exams**: com gabarito oficial → avaliação **exata**

| Métrica      | O que mede                                                 |
|--------------|------------------------------------------------------------|
| **Acurácia** | Proporção de respostas corretas sobre o total              |
| **Precisão** | Quantas vezes o modelo acertou ao escolher uma alternativa |
| **Recall**   | Quantas questões da classe correta foram identificadas     |
| **F1-Score** | Média harmônica entre precisão e recall                    |

- As letras (A, B, C, D) são convertidas para inteiros antes do cálculo
- Estratégia **macro**: calcula a métrica por classe e tira a média simples
