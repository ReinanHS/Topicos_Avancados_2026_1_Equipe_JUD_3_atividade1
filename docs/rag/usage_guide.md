---
sidebar_position: 5
---

# Guia de execução

Este guia prático ensina como preparar o ambiente, executar a indexação da legislação e validar os resultados do RAG.

---

## Pré-requisitos

1. **Ollama Iniciado**: O serviço do Ollama deve estar ativo no computador local.
   - Verifique no tray ou terminal se o Ollama está respondendo em: `http://127.0.0.1:11434`
2. **Dependências Instaladas**: O projeto utiliza `uv` para gerenciar dependências. Se você baixou o código agora, certifique-se de sincronizar o ambiente executando:
   ```bash
   uv sync
   ```

---

## 1. Salvando Legislação no ChromaDB (População)

Para processar todos os arquivos HTML de legislação presentes na pasta `database/rag`, gerar os embeddings e gravá-los no banco de dados vetorial, execute o seguinte comando no terminal:

```bash
uv run reinan-cli rag-populate
```

### Opções Disponíveis
O comando possui argumentos opcionais configuráveis no Typer:
- `--db-path`: Define o diretório onde os dados do ChromaDB serão gravados. Padrão: `.reinan_cache/chromadb`.
- `--collection`: Define o nome da tabela/coleção vetorial. Padrão: `legislacao`.
- `--model`: Define o modelo de embedding a ser invocado no Ollama. Padrão: `qwen3-embedding:8b`.

**Exemplo de uso customizado**:
```bash
uv run reinan-cli rag-populate --collection minha_colecao_leis --model qwen3-embedding:8b
```

### O que acontece por baixo dos panos?
- O terminal listará todos os arquivos HTML encontrados.
- Cada arquivo será limpo e recortado a nível de artigos pelo `LegislationChunker`.
- O Ollama será contatado para gerar os embeddings em lote (se o modelo `qwen3-embedding:8b` não estiver instalado localmente, ele fará o download automático primeiro).
- Os registros serão salvos no ChromaDB e o total indexado será impresso no final.

---

## 2. Executando Consultas de Validação (Buscas e Fatiamento)

Para validar o funcionamento do RAG, existem dois comandos CLI embutidos no projeto:

### Comando `rag-query` (Busca Semântica)
Esse comando executa consultas semânticas por similaridade na base indexada. Por padrão, se nenhum parâmetro for fornecido, ele rodará um conjunto de perguntas comuns de teste (direitos do consumidor, improbidade administrativa, abuso de autoridade).

Para executar as consultas padrão:
```bash
uv run reinan-cli rag-query
```

Para fazer uma pergunta personalizada:
```bash
uv run reinan-cli rag-query --query "Quais são as fases da licitação?" --top-k 3
```

- `--query` / `-q`: A pergunta ou termo que você deseja buscar.
- `--top-k` / `-k`: A quantidade máxima de artigos mais relevantes a serem exibidos. Padrão: `3`.

---

### Comando `rag-test-chunker` (Validação de Fatiamento)
Esse comando testa o processo de quebra de texto (chunking) estrutural sem precisar gerar embeddings ou persistir dados no banco. É excelente para validar se a quebra de artigos e parágrafos de um HTML específico está correta.

Para testar todos os arquivos da pasta:
```bash
uv run reinan-cli rag-test-chunker
```

Para testar um arquivo de lei específico e exibir mais linhas de preview:
```bash
uv run reinan-cli rag-test-chunker --file L14133.html --preview-limit 10
```

- `--file` / `-f`: Nome do arquivo em `database/rag` (ex: `L13869.html`).
- `--preview-limit` / `-p`: Número de linhas de texto do artigo exibidas no preview. Padrão: `5`.

### Comando `rag-test-regression` (Teste de Regressão)
Esse comando executa uma rotina automatizada para garantir que o sistema RAG recupere corretamente a resposta da Questão `2016-21_38`. O teste valida se o Artigo 156 do Código Civil (estado de perigo) fica classificado no topo, enquanto artigos de contrato de transporte (como o Artigo 739, 740 e 742 do Código Civil) recebem penalidade e são rebaixados na lista final.

Para executar o teste de regressão:
```bash
uv run reinan-cli rag-test-regression
```

Opções adicionais:
- `--db-path`: Diretório local do banco ChromaDB. Padrão: `.reinan_cache/chromadb`.
- `--collection`: Nome da coleção no banco. Padrão: `legislacao`.
- `--model`: Modelo de embedding utilizado no Ollama. Padrão: `qwen3-embedding:8b`.


---

## 3. Executando Inferência com RAG

Você pode executar o processo de inferência enriquecendo as perguntas com o contexto recuperado do banco de dados vetorial usando a flag `--rag`.

```bash
uv run reinan-cli infer oab_bench --model qwen2.5:3b --limit 1 --rag
```

### O que acontece quando `--rag` está ativo?
1. Para cada questão processada, o CLI extrai o enunciado da questão.
2. Faz uma busca semântica no ChromaDB para recuperar os artigos de lei mais relevantes relacionados ao tema.
3. Adiciona os artigos recuperados como contexto no prompt que é enviado ao LLM.
4. O modelo responde a questão baseando-se no contexto legal fornecido, o que aumenta a precisão e reduz alucinações.


---

## Solução de Problemas (Troubleshooting)

### Erro: "Falha de conexão com Ollama" ou similar
- **Causa**: O motor local do Ollama não está ativo ou está travado.
- **Solução**: Reinicie o aplicativo Ollama no computador. Teste o acesso abrindo `http://127.0.0.1:11434` no navegador.

### Erro: "SQLite3 lock" ou corrupção no banco de dados vetorial
- **Causa**: Duas instâncias de scripts podem ter tentado escrever no banco simultaneamente.
- **Solução**: Exclua a pasta `.reinan_cache/chromadb` do seu sistema e execute o comando `uv run reinan-cli rag-populate` novamente para reconstruir a base a partir dos HTMLs limpos.
