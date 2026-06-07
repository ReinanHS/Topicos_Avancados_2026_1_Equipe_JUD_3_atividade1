import re
import unicodedata
import chromadb
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.rag.embeddings import OllamaEmbeddingProvider
from src.rag.lexical import LexicalRetriever


def strip_accents(text: str) -> str:
    """Remove acentuação de uma string."""
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


class LegislationVectorDB:
    """
    Interface com o banco de dados vetorial ChromaDB e buscador híbrido.
    Persiste os chunks de legislação, realiza buscas híbridas e aplica reranking.
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
        self.collection = self.client.get_or_create_collection(name=collection_name)

        # Inicializadores para busca lexical
        self._cached_chunks = None
        self._lexical_retriever = None

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
            try:
                self.client.delete_collection(name=collection_name)
            except Exception:
                pass
            self.collection = self.client.get_or_create_collection(name=collection_name)

        if not chunks:
            print("[LegislationVectorDB] Lista de chunks vazia. Nada a inserir.")
            return

        # Limpa os caches em memória
        self._cached_chunks = None
        self._lexical_retriever = None

        print(
            f"[LegislationVectorDB] Iniciando a geração de embeddings para {len(chunks)} chunks..."
        )

        # Extrai os textos para gerar embeddings (usando o campo 'text' que contém contextualização)
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

            # Formata palavras-chave como string separada por vírgula para persistência
            keywords_str = ",".join(chunk.get("keywords", []))

            metadatas.append(
                {
                    "article": chunk["article"],
                    "article_number": chunk.get("article_number", ""),
                    "raw_text": chunk.get("raw_text", chunk["text"]),
                    "law_title": chunk["law_title"],
                    "file_name": chunk["file_name"],
                    "legal_area": chunk.get("legal_area", ""),
                    "keywords": keywords_str,
                    "heading_path": chunk.get("heading_path", ""),
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

    def _get_all_chunks(self) -> List[Dict[str, Any]]:
        """Recupera todos os chunks indexados no ChromaDB."""
        if self._cached_chunks is not None:
            return self._cached_chunks

        try:
            res = self.collection.get(include=["documents", "metadatas"])
            chunks = []
            if res and "documents" in res and res["documents"]:
                docs = res["documents"]
                metas = res["metadatas"]
                ids = res["ids"]
                for i in range(len(docs)):
                    # Converte de volta keywords para lista
                    meta = metas[i] or {}
                    kws = meta.get("keywords", "")
                    keywords_list = kws.split(",") if kws else []

                    chunks.append(
                        {
                            "id": ids[i],
                            "text": docs[i],
                            "raw_text": meta.get("raw_text", docs[i]),
                            "metadata": meta,
                            "keywords": keywords_list,
                            "article": meta.get("article", ""),
                            "article_number": meta.get("article_number", ""),
                            "law_title": meta.get("law_title", ""),
                            "file_name": meta.get("file_name", ""),
                            "legal_area": meta.get("legal_area", ""),
                            "heading_path": meta.get("heading_path", ""),
                        }
                    )
            self._cached_chunks = chunks
            return chunks
        except Exception as e:
            print(f"[LegislationVectorDB] Erro ao carregar todos os chunks: {e}")
            return []

    def _ensure_lexical_retriever(self) -> None:
        """Inicializa e treina o buscador lexical caso ainda não esteja pronto."""
        if self._lexical_retriever is not None:
            return

        chunks = self._get_all_chunks()
        self._lexical_retriever = LexicalRetriever()
        self._lexical_retriever.fit(chunks)

    def _get_available_llm_model(self) -> str:
        """Auto-detecta um modelo LLM instalado no Ollama local para reescrita de query."""
        try:
            models_list = self.embedding_provider.client.list()
            downloaded = [m.model for m in models_list.models]
            # Prioriza modelos comuns pequenos instalados
            for preferred in [
                "gemma2:2b",
                "llama3.2:3b",
                "qwen2.5:3b",
                "gemma2",
                "llama3.2",
                "qwen2.5",
            ]:
                for d in downloaded:
                    if preferred in d:
                        return d
            if downloaded:
                return downloaded[0]
        except Exception:
            pass
        return "gemma2:2b"

    def build_legal_query(self, q: Any, model: Optional[str] = None) -> str:
        """
        Gera uma query jurídica otimizada a partir da questão, ramo do Direito
        e alternativas, filtrando ruídos narrativos.
        """
        # Se 'q' já for uma string simples, retorna ela mesma
        if isinstance(q, str):
            return q

        statement = q.get("question", q.get("statement", ""))
        choices = q.get("choices", {})
        choices_text = ""
        if choices and "text" in choices:
            choices_text = "\n".join(f"- {t}" for t in choices["text"])

        system_prompt = (
            "Você é um assistente especialista em direito brasileiro.\n"
            "Sua tarefa é analisar uma questão de múltipla escolha e extrair uma 'query jurídica' curta e densa para busca (RAG) em códigos de leis.\n"
            "A query jurídica deve:\n"
            "1. Priorizar o ramo do Direito (ex: Direito Civil, Direito Penal, etc.).\n"
            "2. Priorizar os institutos jurídicos centrais envolvidos (ex: estado de perigo, dolo, coação, evicção, erro, nulidade).\n"
            "3. Incluir verbos jurídicos importantes da questão (ex: anular, indenizar, prescrever, executar, impugnar).\n"
            "4. Incluir termos jurídicos chaves presentes nas alternativas.\n"
            "5. Ignorar ou minimizar termos puramente narrativos do caso concreto que não possuem relevância jurídica direta (como 'viagem aérea', 'piscina', 'pizzaria', 'passageiro', 'aeroporto', nomes de pessoas, etc.).\n\n"
            "Retorne APENAS a query jurídica reescrita (uma lista de termos e conceitos separados por espaço), sem explicações, preâmbulos, aspas ou formatação markdown."
        )

        user_prompt = f"Questão: {statement}\n"
        if choices_text:
            user_prompt += f"Alternativas:\n{choices_text}\n"
        user_prompt += "\nQuery jurídica gerada:"

        # Descarta o modelo se for um modelo de embedding
        if model and ("embed" in model.lower() or "nomic" in model.lower()):
            llm_model = self._get_available_llm_model()
        else:
            llm_model = model or self._get_available_llm_model()

        try:
            response = self.embedding_provider.client.chat(
                model=llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            rewritten = response["message"]["content"].strip()
            # Remove quebras de linha e limpa markdown
            rewritten = re.sub(r"\s+", " ", rewritten)
            rewritten = (
                rewritten.replace("`", "")
                .replace("*", "")
                .replace("Query jurídica gerada:", "")
                .strip()
            )
            if rewritten:
                # Augmenta a query com as opções para busca consciente
                clean_choices = []
                if choices and "text" in choices:
                    for opt in choices["text"]:
                        opt_norm = strip_accents(opt).lower().strip(". ")
                        if len(opt_norm) > 3:
                            clean_choices.append(opt_norm)
                if clean_choices:
                    rewritten += " " + " ".join(clean_choices)
                print(
                    f"[RAG] Query jurídica reescrita e aumentada: '{rewritten}' (via {llm_model})"
                )
                return rewritten
        except Exception as e:
            print(
                f"[RAG] Erro ao chamar LLM para reescrita: {e}. Usando fallback por heurística."
            )

        # Fallback de heurística estática se o LLM falhar
        fallback_terms = []
        legal_terms = [
            "estado de perigo",
            "coacao",
            "dolo",
            "erro",
            "lesao",
            "fraude",
            "simulacao",
            "anulabilidade",
            "anulacao",
            "nulidade",
            "nulo",
            "anulavel",
        ]
        text_lower = strip_accents(statement).lower()
        for term in legal_terms:
            if term in text_lower:
                fallback_terms.append(term)

        # Adiciona termos das alternativas diretamente à query de fallback
        if choices and "text" in choices:
            for opt in choices["text"]:
                opt_norm = strip_accents(opt).lower().strip(". ")
                if len(opt_norm) > 3 and opt_norm not in fallback_terms:
                    fallback_terms.append(opt_norm)

        # Adiciona área/categoria
        area = q.get("area", q.get("category", ""))
        if area:
            fallback_terms.append(area)

        if not fallback_terms:
            return statement[:150]

        fallback_query = " ".join(fallback_terms)
        print(f"[RAG] Query jurídica de fallback: '{fallback_query}'")
        return fallback_query

    def query(
        self,
        q: Any,
        top_k: int = 3,
        top_k_retrieval: int = 100,
        top_k_final: Optional[int] = None,
        model: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Pesquisa híbrida com reranking na base de legislação.

        Args:
            q: Questão (dicionário completo) ou texto bruto da consulta.
            top_k: Número final de resultados (caso top_k_final não seja informado).
            top_k_retrieval: Quantidade de documentos a recuperar inicialmente.
            top_k_final: Quantidade final de documentos a retornar.
            model: Nome do modelo de LLM para reescrita de query.
        """
        k_final = top_k_final or top_k

        # Etapa A — Construção da Query Jurídica
        legal_query = self.build_legal_query(q, model)

        # 1. Recuperação Vetorial (ChromaDB)
        query_vector = self.embedding_provider.embed_query(legal_query)
        vector_res = self.collection.query(
            query_embeddings=[query_vector], n_results=top_k_retrieval
        )

        candidates = {}

        if vector_res and "documents" in vector_res and vector_res["documents"]:
            docs = vector_res["documents"][0]
            metas = vector_res["metadatas"][0]
            ids = vector_res["ids"][0]
            distances = vector_res.get("distances", [[]])[0]

            for i in range(len(docs)):
                # Normaliza distância L2 para similaridade (0 a 1)
                dist = distances[i] if i < len(distances) else 0.5
                sim_score = 1.0 / (1.0 + dist)

                doc_id = ids[i]
                candidates[doc_id] = {
                    "id": doc_id,
                    "text": docs[i],
                    "metadata": metas[i] or {},
                    "vector_score": sim_score,
                    "lexical_score": 0.0,
                }

        # 2. Recuperação Lexical (TF-IDF)
        self._ensure_lexical_retriever()
        lexical_res = self._lexical_retriever.search(legal_query, top_k=top_k_retrieval)

        for item in lexical_res:
            doc_id = item["id"]
            lex_score = item["lexical_score"]

            if doc_id in candidates:
                candidates[doc_id]["lexical_score"] = lex_score
            else:
                candidates[doc_id] = {
                    "id": doc_id,
                    "text": item["text"],
                    "metadata": item["metadata"],
                    "vector_score": 0.0,
                    "lexical_score": lex_score,
                }

        # 3. Combinação de Scores (Score Híbrido Base)
        candidate_list = list(candidates.values())
        for c in candidate_list:
            c["base_score"] = 0.5 * c["vector_score"] + 0.5 * c["lexical_score"]

        # Injeção de candidatos adicionais a partir de termos das alternativas
        all_chunks = self._get_all_chunks()
        choices = q.get("choices", {}) if isinstance(q, dict) else {}
        if choices and "text" in choices:
            for alt in choices["text"]:
                alt_norm = strip_accents(alt).lower().strip(". ")
                if len(alt_norm) > 3:
                    for chunk in all_chunks:
                        chunk_text = strip_accents(chunk["text"]).lower()
                        if alt_norm in chunk_text:
                            doc_id = chunk["id"]
                            if doc_id not in candidates:
                                c_entry = {
                                    "id": doc_id,
                                    "text": chunk["text"],
                                    "metadata": chunk["metadata"],
                                    "vector_score": 0.0,
                                    "lexical_score": 0.0,
                                    "base_score": 0.0,
                                }
                                candidates[doc_id] = c_entry
                                candidate_list.append(c_entry)

        # 4. Reranking por Heurísticas (Etapa C)
        reranked = self.rerank(q, candidate_list)

        # Ordena por score decrescente
        reranked.sort(key=lambda x: x["score"], reverse=True)

        return reranked[:k_final]

    def rerank(self, q: Any, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Aplica regras de boost e penalidade com base no domínio jurídico brasileiro.
        Esta estrutura está desacoplada permitindo plugar um reranker neural futuramente.
        """
        # Se 'q' for apenas uma string simples, retorna os scores base sem boosts adicionais
        if isinstance(q, str):
            for c in candidates:
                c["score"] = c["base_score"]
                c["rerank_reason"] = "Score híbrido base (busca vetorial + lexical)."
            return candidates

        q_area = q.get("area", q.get("category", ""))
        choices = q.get("choices", {})

        for c in candidates:
            meta = c["metadata"]
            text_raw = meta.get("raw_text", c["text"])
            text_norm = strip_accents(text_raw).lower()

            boost = 0.0
            penalty = 0.0
            reasons = []

            # A. Correspondência de Área Jurídica
            chunk_area = meta.get("legal_area", "")
            if q_area and chunk_area:
                norm_q_area = strip_accents(q_area).lower()
                norm_chunk_area = strip_accents(chunk_area).lower()
                if norm_q_area in norm_chunk_area or norm_chunk_area in norm_q_area:
                    boost += 0.25
                    reasons.append("Área jurídica compatível (+0.25)")

            # B. Correspondência com termos jurídicos das Alternativas
            matched_alts = []
            alt_boost = 0.0
            if choices and "text" in choices:
                for alt in choices["text"]:
                    alt_norm = strip_accents(alt).lower().strip(". ")
                    # Ignora termos de preenchimento muito curtos
                    if len(alt_norm) > 3:
                        if alt_norm in text_norm:
                            matched_alts.append(alt)
                            # Dá boost maior para termos compostos (multi-palavras)
                            if " " in alt_norm:
                                alt_boost += 0.85
                            else:
                                alt_boost += 0.35

            if matched_alts:
                boost += alt_boost
                reasons.append(
                    f"Contém termo das alternativas: {matched_alts} (+{alt_boost:.2f})"
                )

            # C. Penalização de termos puramente narrativos/cenográficos
            narrative_terms = [
                "viagem",
                "passageiro",
                "piloto",
                "aeroporto",
                "piscina",
                "quadra",
                "pizzaria",
                "pizzas",
                "motociclista",
                "voo",
                "aeronave",
                "surto",
                "remedio",
            ]
            matched_narrative = [w for w in narrative_terms if w in text_norm]

            if matched_narrative:
                # Verifica se o chunk possui algum dos conceitos jurídicos das alternativas
                # Se só tem termos de cenário, mas não trata dos institutos do problema, penaliza
                choices_terms = []
                if choices and "text" in choices:
                    choices_terms = [
                        strip_accents(t).lower().strip(". ") for t in choices["text"]
                    ]

                has_legal_concept = any(
                    term in text_norm for term in choices_terms if len(term) > 3
                )

                if not has_legal_concept:
                    # Penaliza fortemente se contiver narrativa e nenhum termo jurídico relevante
                    penalty_val = 0.50 * len(matched_narrative)
                    penalty += penalty_val
                    reasons.append(
                        f"Contém apenas narrativa ({matched_narrative}) sem termo jurídico chave (-{penalty_val:.2f})"
                    )

            # Calcula score final
            final_score = c["base_score"] + boost - penalty
            # Evita score negativo
            c["score"] = max(0.0, final_score)

            # Registra a justificativa do reranking
            c["rerank_reason"] = (
                "; ".join(reasons) if reasons else "Mantido score híbrido base."
            )

            # Detalhamento para exibição no tester.py
            c["boost"] = boost
            c["penalty"] = penalty

        return candidates

    def count(self) -> int:
        """Retorna a quantidade de registros na coleção."""
        return self.collection.count()
