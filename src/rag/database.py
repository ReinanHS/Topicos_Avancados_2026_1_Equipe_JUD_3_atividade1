import chromadb
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.rag.embeddings import OllamaEmbeddingProvider


class LegislationVectorDB:
    """
    Interface com o banco de dados vetorial ChromaDB.
    Persiste os chunks de legislação e realiza buscas por similaridade semântica.
    """

    def __init__(
        self,
        db_path: str = ".reinan_cache/chromadb",
        collection_name: str = "legislacao",
        embedding_provider: Optional[OllamaEmbeddingProvider] = None,
    ):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Inicializa o cliente persistente do ChromaDB
        self.client = chromadb.PersistentClient(path=str(self.db_path))

        # Associa o gerador de embeddings (cria o padrão caso não seja fornecido)
        self.embedding_provider = embedding_provider or OllamaEmbeddingProvider()

        # Obtém ou cria a coleção no ChromaDB
        # NOTA: Não passamos embedding_function para a coleção pois passamos os embeddings
        # computados explicitamente durante a inserção e busca.
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def populate(self, chunks: List[Dict[str, Any]], reset: bool = False) -> None:
        """
        Gera os embeddings e salva os chunks de legislação no banco vetorial.

        Args:
            chunks: Lista de dicionários contendo os dados dos artigos.
            reset: Se True, recria/limpa a coleção antes de inserir.
        """
        if reset:
            # Limpa a coleção existente excluindo e recriando
            collection_name = self.collection.name
            self.client.delete_collection(name=collection_name)
            self.collection = self.client.get_or_create_collection(name=collection_name)

        if not chunks:
            print("[LegislationVectorDB] Lista de chunks vazia. Nada a inserir.")
            return

        print(
            f"[LegislationVectorDB] Iniciando a geração de embeddings para {len(chunks)} chunks..."
        )

        # Extrai os textos para gerar embeddings
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embedding_provider.embed_documents(texts)

        # Monta os vetores de dados para inserção no ChromaDB
        ids = []
        documents = []
        metadatas = []

        for idx, chunk in enumerate(chunks):
            # Cria um ID único para cada chunk baseado na lei, artigo e índice
            doc_id = f"{chunk['file_name']}_{chunk['article']}_{idx}"
            ids.append(doc_id)
            documents.append(chunk["text"])
            metadatas.append(
                {
                    "article": chunk["article"],
                    "law_title": chunk["law_title"],
                    "file_name": chunk["file_name"],
                }
            )

        # Insere em lotes (batching) no ChromaDB para evitar limites de carga
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            end_idx = min(i + batch_size, len(ids))

            self.collection.add(
                ids=ids[i:end_idx],
                embeddings=embeddings[i:end_idx],
                documents=documents[i:end_idx],
                metadatas=metadatas[i:end_idx],
            )
            print(f"[LegislationVectorDB] Indexados {end_idx}/{len(ids)} chunks...")

        print(
            f"[LegislationVectorDB] População concluída com sucesso! Total de itens: {self.collection.count()}"
        )

    def query(self, text_query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Pesquisa no banco vetorial pelos trechos de lei mais semelhantes à pergunta.

        Returns:
            Lista de dicionários contendo o texto recuperado, metadados e score de proximidade.
        """
        # Gera o embedding da pergunta
        query_vector = self.embedding_provider.embed_query(text_query)

        # Consulta a coleção
        results = self.collection.query(
            query_embeddings=[query_vector], n_results=top_k
        )

        formatted_results = []

        # A resposta do ChromaDB vem estruturada em listas aninhadas
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            ids = results["ids"][0]
            # Algumas versões do ChromaDB podem não retornar distâncias dependendo da métrica
            distances = results.get("distances", [[]])[0]

            for i in range(len(docs)):
                formatted_results.append(
                    {
                        "id": ids[i],
                        "text": docs[i],
                        "metadata": metas[i],
                        "score": distances[i] if i < len(distances) else 0.0,
                    }
                )

        return formatted_results

    def count(self) -> int:
        """Retorna a quantidade de registros na coleção."""
        return self.collection.count()
