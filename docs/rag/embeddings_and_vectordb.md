---
sidebar_position: 3
---

# Embeddings e banco de dados vetorial

Esta seção explica a lógica por trás da geração de vetores de alta dimensão e da persistência de dados utilizando o **ChromaDB** e o **Ollama**.

---

## Geração de Embeddings em Português

A geração de embeddings mapeia trechos textuais (artigos de lei) para vetores numéricos em um espaço vetorial contínuo, onde textos com significados parecidos ficam geograficamente próximos.

### Escolha do Modelo: `qwen3-embedding:8b`
Selecionamos o modelo **`qwen3-embedding:8b`** executado localmente através da API do **Ollama** pelos seguintes motivos:
- **Janela de Contexto Expandida**: Suporta até **8.192 tokens** de entrada, o que é ideal para artigos extensos (como o Artigo 5º da Constituição ou o Artigo 6º do Código de Defesa do Consumidor).
- **Multilíngue**: Excelente desempenho de similaridade em português, capturando sinônimos jurídicos (ex: mapeando "contratação" para "licitação").
- **Execução Local**: Dispensa chaves de API pagas e permite que o ecossistema rode offline, aproveitando aceleração de GPU ou CPU local.

### Gestão Automática do Ciclo de Vida (`OllamaEmbeddingProvider`)
No arquivo `src/rag/embeddings.py`, criamos um gerenciador robusto:
- **Auto-Pull**: Durante a inicialização, o provedor consulta a API do Ollama. Caso o modelo `qwen3-embedding:8b` não esteja baixado, o script inicia o download (`client.pull()`) de forma transparente, garantindo que o comando funcione no computador de qualquer usuário sem configurações prévias manuais.
- **Robustez com Loteamento (Batching)**: Ao indexar mais de 4.000 artigos de uma só vez, o Ollama pode sofrer estrangulamento de memória. Nosso código divide a carga em lotes seguros de 32 trechos. Em caso de falha de conexão em um lote, o provedor tenta gerar os vetores individualmente, isolando trechos defeituosos e garantindo que o pipeline não seja interrompido.

---

## Persistência de Dados com ChromaDB

O **ChromaDB** foi selecionado como banco de dados vetorial local do projeto por ser leve, persistente em disco e de fácil integração em Python.

### Configuração da Conexão
Toda a lógica está encapsulada em `src/rag/database.py`. O banco é configurado no modo persistente apontando para o diretório de cache local do projeto:
`.reinan_cache/chromadb`

Isso gera arquivos SQLite locais que salvam os índices espaciais HNSW e os metadados. Da próxima vez que o sistema iniciar, ele lerá os vetores do disco sem a necessidade de reprocessar os HTMLs e recalcular embeddings, economizando tempo e energia.

### Estruturação de Dados e Inserção

Para cada artigo inserido, estruturamos os seguintes campos:
- **ID**: String única gerada no formato `{nome_do_arquivo}_{artigo}_{indice_unico}` (ex: `L13869.html_Art. 1_315`).
- **Embedding**: Vetor de 768 dimensões gerado pelo Ollama.
- **Document**: Texto limpo completo do artigo.
- **Metadatas**: Dicionário com informações estruturais:
  - `article`: Código formatado do artigo (ex: `"Art. 1"`).
  - `law_title`: Título formatado e amigável da lei (ex: `"Lei de Abuso de Autoridade (Lei 13.869/2019)"`).
  - `file_name`: Nome original do arquivo HTML (ex: `"L13869.html"`).

A inserção no ChromaDB também é feita em sub-lotes de 100 registros para evitar sobrecarga no conector SQLite.

---

## Busca por Similaridade Semântica

A busca utiliza a distância vetorial calculada entre o embedding da consulta do usuário e o embedding dos artigos persistidos. 

Ao efetuar uma query:
1. O texto da consulta é enviado ao provedor de embeddings, que retorna seu vetor correspondente.
2. O ChromaDB realiza a busca pelos `top-k` vetores mais próximos (usando distância L2/cosseno).
3. O banco retorna o texto dos artigos juntamente com seus metadados (permitindo ao LLM saber exatamente qual lei e qual artigo está citando) e o score de distância (quanto menor, mais semelhante).
