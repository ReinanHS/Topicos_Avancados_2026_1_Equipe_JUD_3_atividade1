---
sidebar_position: 1
---

# Ecossistema RAG

Bem-vindo à documentação do sistema de **Geração Aumentada por Recuperação (RAG)** implementado para o domínio de legislação brasileira. Esta documentação detalha a arquitetura, as escolhas de projeto e as instruções de execução para o nosso pipeline.

O objetivo do RAG é municiar os modelos de linguagem locais (como Qwen, Gemma e Llama) com trechos de leis brasileiras altamente relevantes e atualizadas, minimizando alucinações de fatos e contornando a limitação de data de corte (*knowledge cutoff*) dos pesos internos dos modelos.

---

## Organização da Documentação

A documentação está dividida nos seguintes tópicos detalhados:

1. **[Estratégia de Quebra de Texto (Chunking)](chunking_strategy.md)**
   - Discussão dos desafios de parser de arquivos HTML do domínio legislativo (como os do site do Planalto).
   - Detalhes do pré-processador BeautifulSoup e o algoritmo linear baseado em artigos (`LegislationChunker`).
   
2. **[Embeddings e Banco de Dados Vetorial](embeddings_and_vectordb.md)**
   - Explicação sobre a escolha do modelo de embeddings local em português (`nomic-embed-text` via Ollama).
   - Detalhes sobre a modelagem de dados, loteamento (*batching*) e a persistência no **ChromaDB**.

3. **[Guia de Execução e Testes](usage_guide.md)**
   - Instruções passo a passo de como rodar o comando CLI para indexar a legislação.
   - Como executar buscas rápidas de teste semântico por terminal.

---

## Resumo da Arquitetura do Componente

A arquitetura do RAG foi implementada dentro do subdiretório exclusivo `src/rag/` com a seguinte estrutura:

```
src/rag/
├── __init__.py          # Inicialização do pacote
├── chunker.py           # Divisor estrutural de HTML de leis em artigos
├── embeddings.py        # Provedor de vetores de alta dimensão usando Ollama
└── database.py          # Interface com o banco vetorial persistente ChromaDB
```

Toda a persistência local da base vetorial do ChromaDB fica localizada na pasta de cache do projeto em `.reinan_cache/chromadb`.
