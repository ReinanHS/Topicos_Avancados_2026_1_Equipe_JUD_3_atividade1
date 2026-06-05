---
sidebar_position: 10
---

# Atividade 3

Avaliação de Impacto de Recuperação Avançada (RAG) e Resolução Temporal em Domínios de Alta Especialidade

## 1. Contexto e Objetivo

Um dos grandes limites dos modelos de linguagem locais ou de menor escala testados na Atividade 1 é o conhecimento estático e a tendência a alucinações fáticas em dados muito específicos. Além disso, a temporalidade, como leis modificadas, novas decisões de tribunais superiores ou consensos médicos atualizados, pode tornar obsoletos os pesos internos de um modelo congelado.

O objetivo desta atividade é: evoluir o ecossistema construído pelas equipes aplicando o conceito de **RAG-as-a-Judge** e **RAG Base**. Cada equipe deverá implementar uma arquitetura de **Geração Aumentada por Recuperação (RAG)** para municiar os mesmos modelos selecionados e testados na Atividade 1 com documentos técnicos altamente atualizados, medindo o impacto fático e temporal nas respostas, tanto abertas quanto de múltipla escolha.

## 2. Repositórios de Dados e Temas

As equipes mantêm estritamente os mesmos conjuntos de dados e a distribuição de componentes já consolidada:

- ⚖️ **Domínio Jurídico (Equipes 1, 3 e 4):** Datasets J1 (`oab-bench`) e J2 (`oab_exams`).
- 🩺 **Domínio Médico (Equipes 2 e 5):** Datasets M1 (`K-QA`) e M2 (`USMLE`).

## 3. Etapas Previstas na Atividade

### Passo 1: Curadoria de Documentação Externa e Justificativa (O Cérebro do RAG)

Cada equipe deve selecionar ativamente um corpo de documentos externos em formato texto/PDF para alimentar a base de vetores do RAG.

- **Critério de Inclusão:** A equipe deve listar e justificar textualmente no relatório quais critérios utilizou para escolher tais documentos. Exemplos: manuais de diretrizes da SBC/AHA posteriores ao ano de corte do modelo, atualizações do Código Penal e jurisprudências do STF/STJ recentes.
- **Fator Temporalidade:** É obrigatório incluir pelo menos um conjunto de documentos que represente atualizações de conhecimento que o modelo não possuía nativamente em seus pesos por questões de data de corte (*knowledge cutoff*).

### Passo 2: Implementação da Arquitetura RAG

Implementar um pipeline local ou via API contendo:

1. Um componente de quebra de texto (*chunking*) e geração de embeddings.
2. Uma base vetorial, por exemplo: ChromaDB, FAISS ou a própria extensão `pgvector` acoplada ao PostgreSQL já estruturado na Atividade 2.
3. Um mecanismo de busca por similaridade que capture os `top-k` fragmentos mais relevantes para a pergunta original do estudante.

### Passo 3: Re-Inferência dos Modelos de Linguagem

Submeter as perguntas originais novamente aos mesmos modelos de linguagem da Atividade 1, mas agora incluindo no contexto do prompt os fragmentos recuperados pelo RAG.

### Passo 4: Nova Avaliação Automatizada (LLM-as-a-Judge pós-RAG)

Utilizando o ecossistema da Atividade 2, rode novamente o seu pipeline com o modelo Juiz para avaliar as respostas geradas com suporte do RAG.

- **Casos de Teste:** O banco de dados PostgreSQL deve ser atualizado para permitir a comparação direta: `Nota_Juiz_Sem_RAG` contra `Nota_Juiz_Com_RAG`.
- O juiz deve usar o campo **Chain-of-Thought** para determinar se o RAG ajudou a corrigir uma alucinação ou se trouxe ruído para a resposta.

### Passo 5: Análise Estatística de Evolução

Calcule os novos coeficientes de correlação de Spearman (ρ) e avalie se houve ganho estatístico de desempenho em relação ao gabarito padrão-ouro humano após a introdução da base de conhecimento.

## 4. Artefatos e Regras de Entrega

📅 **Data Limite para Upload dos Artefatos:** 10 de junho de 2026, quarta-feira, até as 12h00 (meio-dia).

📅 **Apresentações Presenciais:** 11 de junho de 2026, quinta-feira, com participação obrigatória de todos os membros das equipes.

Os representantes oficiais de cada equipe designados nas atividades anteriores realizarão a postagem na thread dedicada do Google Classroom:

- **Equipe 1:** Helena, Rafael.
- **Equipe 2:** Carlos, Gilson Inácio.
- **Equipe 3:** Fernanda Mirely, Mikaela, Victor Leonardo.
- **Equipe 4:** Paulo.
- **Equipe 5:** Marcelo West, Clelio, Sergio Santana, Hernandson Bispo.

### Entregáveis no Repositório Git e Classroom

1. **Tutorial em PDF (Consolidado):** Capa com dados do SIGAA, link do vídeo e declaração explícita de contribuições. Deve detalhar a arquitetura do RAG, os critérios de inclusão dos documentos, as queries SQL executadas e os resultados das correlações estatísticas.
2. **Atualização do Repositório GitHub:** Inclusão da pasta `Atividade_3` contendo os novos scripts Python (pipeline RAG), os prompts de sistema atualizados e o arquivo de backup estruturado (`.sql` ou `.dump`) refletindo os dados antes e depois do RAG.
3. **Vídeo Demonstrativo:** Duração mínima de 10 minutos e máxima de 20 minutos. Cada componente deve demonstrar na IDE ou no terminal a execução da sua fatia de código ou os dados correspondentes à sua curadoria. O link deve estar no `README.md`.

## 5. Barema de Avaliação (Critérios de Nota)

| Critério | Descrição | Peso |
|---|---|---:|
| Arquitetura RAG e Justificativa | Qualidade fática dos documentos escolhidos, tratamento da temporalidade e robustez técnica do componente de busca/recuperação. | 30% |
| Pipeline e Evolução no DB | Adaptação correta do esquema relacional e scripts para comparar o desempenho dos modelos com e sem RAG. | 25% |
| Meta-Avaliação (Juiz) | Qualidade e rigor do prompt do Juiz ao discriminar o ganho gerado pelo RAG via Chain-of-Thought. | 20% |
| Análise Estatística e de Erros | Profundidade na verificação de correlação e identificação de casos onde o RAG falhou ou inseriu ruído. | 15% |
| Apresentação Presencial e Documentação | Domínio do tema demonstrado em sala de aula por todos os componentes e organização dos arquivos. | 10% |

## 💡 Nota de Orientação Pedagógica

Fiquem atentos para não transformar o RAG em um injetor de textos desconexos. O papel do engenheiro de IA e cientista de dados nesta fase é a filtragem qualitativa. Um documento mal selecionado destruirá o coeficiente de correlação do seu modelo e será punido pelo seu próprio agente juiz.

Usem o conhecimento adquirido em sala de aula para arquitetar uma estratégia limpa e defensável na nossa banca presencial. Bons experimentos!
