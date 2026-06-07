from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np


class LexicalRetriever:
    """
    Realiza busca lexical simples baseada em TF-IDF sobre os chunks de legislação.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            token_pattern=r"(?u)\b\w\w+\b",
        )
        self.tfidf_matrix = None
        self.chunks = []

    def fit(self, chunks: List[Dict[str, Any]]) -> None:
        """Ajusta o vetorizador TF-IDF nos textos dos chunks."""
        self.chunks = chunks
        texts = [chunk.get("text", "") for chunk in chunks]
        if texts:
            try:
                self.tfidf_matrix = self.vectorizer.fit_transform(texts)
            except ValueError:
                # Caso ocorra erro se o vocabulário for vazio (ex: só termos sem significado)
                self.tfidf_matrix = None

    def search(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """Realiza a busca pelo texto da query e retorna os trechos mais relevantes."""
        if self.tfidf_matrix is None or not self.chunks:
            return []

        try:
            query_vec = self.vectorizer.transform([query])
            # Calcula a similaridade de cosseno
            scores = (self.tfidf_matrix * query_vec.T).toarray().flatten()

            # Obtém os índices ordenados de forma decrescente
            top_indices = np.argsort(scores)[::-1][:top_k]

            results = []
            for idx in top_indices:
                score = float(scores[idx])
                if score > 0.0:
                    # Retorna uma cópia do chunk com o score lexical adicionado
                    chunk_copy = self.chunks[idx].copy()
                    chunk_copy["lexical_score"] = score
                    results.append(chunk_copy)
            return results
        except Exception as e:
            print(f"[LexicalRetriever] Erro ao realizar busca lexical: {e}")
            return []
