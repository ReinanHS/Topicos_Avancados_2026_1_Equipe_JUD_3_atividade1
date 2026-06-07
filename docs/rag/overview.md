---
sidebar_position: 1
---

# Visão geral do RAG

Bem-vindo à documentação do sistema de **Geração Aumentada por Recuperação (RAG)** implementado para o domínio de legislação brasileira. Esta documentação detalha a arquitetura, as escolhas de projeto e as instruções de execução para o nosso pipeline.

O objetivo do RAG é municiar os modelos de linguagem locais (como Qwen, Gemma e Llama) com trechos de leis brasileiras altamente relevantes e atualizadas, minimizando alucinações de fatos e contornando a limitação de data de corte (*knowledge cutoff*) dos pesos internos dos modelos.

---

## Organização da Documentação

A documentação está dividida nos seguintes tópicos detalhados:

1. **[Estratégia de Quebra de Texto (Chunking)](chunking_strategy.md)**
   - Discussão dos desafios de parser de arquivos HTML do domínio legislativo (como os do site do Planalto).
   - Detalhes do pré-processador BeautifulSoup e o algoritmo linear baseado em artigos (`LegislationChunker`).
   
2. **[Embeddings e Banco de Dados Vetorial](embeddings_and_vectordb.md)**
   - Explicação sobre a escolha do modelo de embeddings local em português (`qwen3-embedding:8b` via Ollama).
   - Detalhes sobre a modelagem de dados, loteamento (*batching*) e a persistência no **ChromaDB**.

3. **[Estratégia de Ranqueamento e Re-ranqueamento (Reranking)](ranking_and_reranking.md)**
   - Funcionamento da fusão híbrida (busca vetorial e busca lexical TF-IDF).
   - Injeção de candidatos relevantes e aplicação das heurísticas de boost por área e alternativas.
   - Aplicação de penalidades para afastar trechos puramente cenográficos/narrativos.

4. **[Guia de Execução e Testes](usage_guide.md)**
   - Instruções passo a passo de como rodar o comando CLI para indexar a legislação.
   - Como executar buscas rápidas de teste semântico por terminal e testes de regressão.

---

## Resumo da Arquitetura do Componente

A arquitetura do RAG foi implementada dentro do subdiretório exclusivo `src/rag/` com a seguinte estrutura:

```
src/rag/
├── __init__.py          # Inicialização do pacote
├── chunker.py           # Divisor estrutural de HTML de leis em artigos
├── database.py          # Interface com a base ChromaDB e lógica de ranqueamento/reranking
├── embeddings.py        # Provedor de embeddings locais usando Ollama
├── lexical.py           # Buscador lexical de suporte baseado em TF-IDF
└── tester.py            # Validador de chunking, consultas diagnósticas e testes de regressão
```

Toda a persistência local da base vetorial do ChromaDB fica localizada na pasta de cache do projeto em `.reinan_cache/chromadb`.

