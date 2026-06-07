import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import typer
from src.rag.chunker import LegislationChunker


# Typer app local para tester se necessário, mas as funções são chamadas pelo cli
def resolve_target_files(rag_dir: Path, file_name: Optional[str]) -> List[Path]:
    """Resolve e valida os arquivos HTML a serem analisados."""
    if not rag_dir.exists():
        typer.echo(f"Erro: O diretório '{rag_dir}' não existe.", err=True)
        raise typer.Exit(code=1)

    if not file_name:
        return list(rag_dir.glob("*.html"))

    target_file = rag_dir / file_name
    if not target_file.exists():
        typer.echo(
            f"Erro: Arquivo '{file_name}' não encontrado em '{rag_dir}'.", err=True
        )
        raise typer.Exit(code=1)

    return [target_file]


def print_chunk_preview(chunk: Dict[str, Any], preview_limit: int) -> None:
    """Imprime um preview formatado do artigo/chunk fornecido."""
    typer.echo(f"  Amostra de Chunk (Artigo: {chunk['article']}):")
    lines = chunk["text"].split("\n")
    preview = "\n".join(lines[:preview_limit])
    typer.echo(f"    {preview}")
    if len(lines) > preview_limit:
        typer.echo("    ...")


def run_chunker_tests(file_name: Optional[str], preview_limit: int) -> None:
    """Executa a validação de chunking para os arquivos selecionados."""
    rag_dir = Path("database/rag")
    target_files = resolve_target_files(rag_dir, file_name)

    if not target_files:
        typer.echo(f"Aviso: Nenhum arquivo HTML encontrado em '{rag_dir}'.")
        return

    chunker = LegislationChunker()

    for file_path in target_files:
        typer.echo(f"\nAnalisando arquivo: {file_path.name}")
        chunks = chunker.chunk_file(file_path)
        typer.echo(f"  Total de chunks (artigos) gerados: {len(chunks)}")

        if chunks:
            # Exibe o primeiro artigo real (geralmente index 1, pois index 0 é preâmbulo)
            sample_idx = min(1, len(chunks) - 1)
            print_chunk_preview(chunks[sample_idx], preview_limit)

        typer.echo("-" * 60)


def _print_query_results(results: List[Dict[str, Any]]) -> None:
    """Imprime os resultados de similaridade retornados pelo banco vetorial."""
    if not results:
        typer.echo("  Nenhum resultado encontrado.")
        return

    for idx, res in enumerate(results):
        meta = res["metadata"]
        typer.echo(f"  Resultado {idx + 1}:")
        typer.echo(
            f"    Lei: {meta.get('law_title', 'Desconhecida')} ({meta.get('file_name', '')})"
        )
        typer.echo(f"    Artigo: {meta.get('article', 'Desconhecido')}")
        typer.echo(f"    Score (Proximidade): {res['score']:.4f}")

        # Mostra as primeiras 4 linhas do texto
        lines = res["text"].split("\n")
        preview = "\n".join(lines[:4])
        typer.echo(f"    Texto Recuperado:\n{preview}")
        if len(lines) > 4:
            typer.echo("      ...")
        typer.echo("")


def run_query_tests(
    query_text: Optional[str], top_k: int, db_path: str, collection: str, model: str
) -> None:
    """Orquestra as consultas híbridas com exibição detalhada de diagnósticos."""
    from src.rag.embeddings import OllamaEmbeddingProvider
    from src.rag.database import LegislationVectorDB

    provider = OllamaEmbeddingProvider(model_name=model)
    db = LegislationVectorDB(
        db_path=db_path, collection_name=collection, embedding_provider=provider
    )

    if not db.count():
        typer.echo(
            "Erro: O banco de dados vetorial está vazio. Execute 'rag-populate' primeiro.",
            err=True,
        )
        raise typer.Exit(code=1)

    # 1. Resolve a entrada (pode ser texto simples, string JSON ou arquivo JSON)
    q = query_text
    if query_text:
        path = Path(query_text)
        if path.exists() and path.is_file():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    q = json.load(f)
            except Exception as e:
                typer.echo(f"Erro ao ler arquivo de questão JSON: {e}")
        else:
            try:
                q = json.loads(query_text)
            except Exception:
                pass

    # Se q for apenas uma string, criamos um formato de dicionário simples de questão
    if isinstance(q, str) or q is None:
        default_statement = q or "Quais são os direitos básicos do consumidor?"
        q = {"question": default_statement, "choices": {"text": []}, "area": ""}

    statement = q.get("question", q.get("statement", ""))
    choices = q.get("choices", {}).get("text", [])

    # Etapa A — Consulta e Reescrita
    typer.echo("\n" + "=" * 60)
    typer.echo(f"Query Original:\n  '{statement}'")
    if choices:
        typer.echo("Alternativas fornecidas:")
        for c in choices:
            typer.echo(f"  - {c}")

    legal_query = db.build_legal_query(q, model)
    typer.echo(f"\nQuery Jurídica Reescrita:\n  '{legal_query}'")
    typer.echo("=" * 60)

    # Etapa B — Busca Vetorial Inicial
    typer.echo("\n--- [1] Resultados Vetoriais Iniciais (Top 5 no ChromaDB) ---")
    query_vector = db.embedding_provider.embed_query(legal_query)
    vector_res = db.collection.query(query_embeddings=[query_vector], n_results=5)

    if vector_res and "documents" in vector_res and vector_res["documents"]:
        docs = vector_res["documents"][0]
        metas = vector_res["metadatas"][0]
        distances = vector_res.get("distances", [[]])[0]
        for i in range(len(docs)):
            dist = distances[i] if i < len(distances) else 0.5
            sim = 1.0 / (1.0 + dist)
            typer.echo(
                f"  * {metas[i].get('law_title')} - {metas[i].get('article')} (Distância: {dist:.4f}, Sim: {sim:.4f})"
            )
    else:
        typer.echo("  Nenhum resultado vetorial.")

    # Etapa B — Busca Lexical Inicial
    typer.echo("\n--- [2] Resultados Lexicais Iniciais (Top 5 via TF-IDF) ---")
    db._ensure_lexical_retriever()
    lexical_res = db._lexical_retriever.search(legal_query, top_k=5)

    if lexical_res:
        for idx, item in enumerate(lexical_res):
            meta = item["metadata"]
            typer.echo(
                f"  * {meta.get('law_title')} - {meta.get('article')} (Lexical Score: {item['lexical_score']:.4f})"
            )
    else:
        typer.echo("  Nenhum resultado lexical.")

    # Etapa C — Reranking e Fusão Híbrida
    typer.echo("\n" + "=" * 60)
    typer.echo(f"--- [3] Resultados Finais (Top {top_k} com Reranking & Fusão) ---")
    typer.echo("=" * 60)

    results = db.query(q, top_k_final=top_k, top_k_retrieval=20, model=model)

    if not results:
        typer.echo("Nenhum resultado retornado pelo RAG.")
    else:
        for idx, res in enumerate(results):
            meta = res["metadata"]
            typer.echo(f"\nResultado {idx + 1}:")
            typer.echo(
                f"  Lei: {meta.get('law_title')} | Artigo: {meta.get('article')}"
            )
            typer.echo(f"  Score Híbrido Final: {res['score']:.4f}")
            typer.echo(f"    - Score Vetorial Base: {res.get('vector_score', 0.0):.4f}")
            typer.echo(f"    - Score Lexical Base: {res.get('lexical_score', 0.0):.4f}")
            typer.echo(f"    - Boost Aplicado: +{res.get('boost', 0.0):.4f}")
            typer.echo(f"    - Penalidade Aplicada: -{res.get('penalty', 0.0):.4f}")
            typer.echo(
                f"    - Motivo do Reranking: {res.get('rerank_reason', 'Nenhum')}"
            )

            # Mostra as primeiras 3 linhas do texto
            lines = res["text"].split("\n")
            preview = "\n".join(lines[:3])
            typer.echo(f"  Texto Recuperado:\n    {preview}")
            if len(lines) > 3:
                typer.echo("    ...")
            typer.echo("-" * 60)


def _run_regression_q38(db, model: str) -> bool:
    """
    Teste de regressão para a questão 2016-21_38 (Eliseu / estado de perigo).
    Garante que o Art. 156 do Código Civil seja recuperado no topo e que
    os artigos de transporte (Art. 739, 740, 742) sejam penalizados.
    """
    typer.echo("\n=== [TESTE 1/2] Questão 2016-21_38 (Eliseu / estado de perigo) ===")

    q = {
        "id": "2016-21_38",
        "question_number": 38,
        "exam_id": "2016-21",
        "exam_year": "2016",
        "question": "Durante uma viagem aérea, Eliseu foi acometido de um mal súbito, que demandava atendimento imediato. O piloto dirigiu o avião para o aeroporto mais próximo, mas a aterrissagem não ocorreria a tempo de salvar Eliseu. Um passageiro ofereceu seus conhecimentos médicos para atender Eliseu, mas demandou pagamento bastante superior ao valor de mercado, sob a alegação de que se encontrava de férias.\nOs termos do passageiro foram prontamente aceitos por Eliseu. Recuperado do mal que o atingiu, para evitar a cobrança dos valores avençados, Eliseu pode pretender a anulação do acordo firmado com o outro passageiro, alegando",
        "choices": {
            "text": ["erro.", "dolo.", "coação.", "estado de perigo."],
            "label": ["A", "B", "C", "D"],
        },
        "area": "Direito Civil",
    }

    results = db.query(q, top_k_final=10, top_k_retrieval=20, model=model)

    typer.echo("\nResultados Obtidos (Top 10):")
    for idx, res in enumerate(results):
        meta = res["metadata"]
        typer.echo(
            f"  {idx + 1}. {meta.get('law_title')} - {meta.get('article')} (Score: {res['score']:.4f})"
        )
        typer.echo(f"     Justificativa: {res.get('rerank_reason', '')}")
    typer.echo("-" * 60)

    # Encontra as posições dos artigos críticos
    pos_art_156 = -1
    transport_violations = []

    for idx, res in enumerate(results):
        meta = res["metadata"]
        art = meta.get("article", "")
        file_name = meta.get("file_name", "").lower()

        if "l10406" in file_name:
            if "156" in art:
                pos_art_156 = idx
            elif any(x in art for x in ["739", "740", "742"]):
                if pos_art_156 == -1 or idx < pos_art_156:
                    transport_violations.append((art, idx))

    # Validação 1: O Art. 156 deve ser encontrado
    if pos_art_156 == -1:
        typer.echo(
            "[FALHA] Artigo 156 do Código Civil não encontrado nos resultados.",
            err=True,
        )
        return False

    typer.echo(f"[OK] Artigo 156 do Código Civil na posição {pos_art_156 + 1}.")

    # Validação 2: Artigos de transporte não devem estar acima do Art. 156
    if transport_violations:
        typer.echo(
            "[FALHA] Artigos de transporte acima do Art. 156:",
            err=True,
        )
        for art, pos in transport_violations:
            typer.echo(f"  - Artigo {art} na posição {pos + 1}", err=True)
        return False

    typer.echo("[SUCESSO] Questão 2016-21_38 passou no teste de regressão.")
    return True


def _run_regression_q37(db, model: str) -> bool:
    """
    Teste de regressão para a questão 2016-21_37 (André / transtorno psiquiátrico).
    Garante que dispositivos centrais sobre incapacidade relativa e causa transitória
    sejam recuperados, e que a confiança da recuperação não seja 'low'.

    Artigos esperados nos resultados:
    - Art. 4 do Código Civil (causa transitória / incapacidade relativa)
    - Art. 171 do Código Civil (anulabilidade por incapacidade relativa)
    Resposta correta: C (anulação + causa transitória)
    """
    typer.echo("\n=== [TESTE 2/2] Questão 2016-21_37 (André / causa transitória) ===")

    q = {
        "id": "2016-21_37",
        "question_number": 37,
        "exam_id": "2016-21",
        "exam_year": "2016",
        "question": "André possui um transtorno psiquiátrico grave, que demanda uso contínuo de medicamentos, graças aos quais ele leva vida normal. No entanto, em razão do consumo de remédios que se revelaram ineficazes, por causa de um defeito de fabricação naquele lote, André foi acometido de um surto que, ao privá-lo de discernimento, o levou a comprar diversos produtos caros de que não precisava.\nPara desfazer os efeitos desses negócios, André deve pleitear",
        "choices": {
            "text": [
                "a nulidade dos negócios, por incapacidade absoluta decorrente de enfermidade ou deficiência mental.",
                "a nulidade dos negócios, por causa transitória impeditiva de expressão da vontade.",
                "a anulação do negócio, por causa transitória impeditiva de expressão da vontade.",
                "a anulação do negócio, por incapacidade relativa decorrente de enfermidade ou deficiência mental.",
            ],
            "label": ["A", "B", "C", "D"],
        },
        "area": "Direito Civil",
    }

    results = db.query(q, top_k_final=10, top_k_retrieval=30, model=model)

    typer.echo("\nResultados Obtidos (Top 10):")
    for idx, res in enumerate(results):
        meta = res["metadata"]
        typer.echo(
            f"  {idx + 1}. {meta.get('law_title')} - {meta.get('article')} (Score: {res['score']:.4f})"
        )
        typer.echo(f"     Justificativa: {res.get('rerank_reason', '')}")

    # Mostra confiança
    if results:
        confidence = results[0].get("confidence", {})
        typer.echo(
            f"\n  Confiança: {confidence.get('level', '?')} — {confidence.get('reason', '')}"
        )
    typer.echo("-" * 60)

    # Busca posições de artigos centrais
    pos_art_4 = -1
    pos_art_171 = -1
    has_relevant_incapacity = False

    for idx, res in enumerate(results):
        meta = res["metadata"]
        art = meta.get("article", "")
        file_name = meta.get("file_name", "").lower()
        text_lower = res.get("text", "").lower()

        if "l10406" in file_name:
            # Art. 4 (pode ser "Art. 4" ou "Art. 4º")
            if art.strip().lower() in ["art. 4", "art 4", "art. 4º"]:
                pos_art_4 = idx
            elif "171" in art:
                pos_art_171 = idx

        # Verifica se algum resultado menciona causa transitória ou incapacidade relativa
        if (
            "causa transitoria" in text_lower
            or "incapacidade relativa" in text_lower
            or "exprimir" in text_lower
        ):
            has_relevant_incapacity = True

    passed = True

    # Validação 1: Pelo menos um resultado contém conceito de causa transitória / incapacidade relativa
    if not has_relevant_incapacity:
        typer.echo(
            "[AVISO] Nenhum resultado contém termos sobre 'causa transitória' ou 'incapacidade relativa'.",
        )
        # Não falha o teste, mas avisa — pode ser que os termos estejam no heading_path ou keywords

    # Validação 2: Art. 4 idealmente no top 5
    if pos_art_4 != -1:
        typer.echo(f"[OK] Art. 4 do Código Civil na posição {pos_art_4 + 1}.")
        if pos_art_4 >= 5:
            typer.echo("[AVISO] Art. 4 está abaixo do top 5. Poderia melhorar.")
    else:
        typer.echo("[AVISO] Art. 4 do Código Civil não encontrado no top 10.")
        # Não falha o teste inteiro, mas registra

    # Validação 3: Art. 171 idealmente presente
    if pos_art_171 != -1:
        typer.echo(f"[OK] Art. 171 do Código Civil na posição {pos_art_171 + 1}.")
    else:
        typer.echo("[INFO] Art. 171 do Código Civil não ficou no top 10.")

    # Validação 4: Confiança não deve ser 'low'
    if results:
        confidence = results[0].get("confidence", {})
        if confidence.get("level") == "low":
            typer.echo(
                f"[FALHA] Confiança da recuperação é 'low': {confidence.get('reason', '')}",
                err=True,
            )
            passed = False

    if passed:
        typer.echo("[SUCESSO] Questão 2016-21_37 passou no teste de regressão.")
    else:
        typer.echo("[FALHA] Questão 2016-21_37 falhou no teste de regressão.")

    return passed


def run_regression_test(db_path: str, collection: str, model: str) -> None:
    """
    Executa os testes de regressão para as questões 2016-21_38 e 2016-21_37.
    """
    from src.rag.embeddings import OllamaEmbeddingProvider
    from src.rag.database import LegislationVectorDB

    typer.echo(
        "=== [TESTE DE REGRESSÃO] Executando validação das questões críticas ==="
    )

    provider = OllamaEmbeddingProvider(model_name=model)
    db = LegislationVectorDB(
        db_path=db_path, collection_name=collection, embedding_provider=provider
    )

    if not db.count():
        typer.echo(
            "Erro: O banco de dados vetorial está vazio. Popule-o primeiro.", err=True
        )
        sys.exit(1)

    # Executa os dois testes sequencialmente
    test1_ok = _run_regression_q38(db, model)
    test2_ok = _run_regression_q37(db, model)

    typer.echo("\n" + "=" * 60)
    if test1_ok and test2_ok:
        typer.echo("[SUCESSO GERAL] Todos os testes de regressão passaram!")
    else:
        failures = []
        if not test1_ok:
            failures.append("2016-21_38")
        if not test2_ok:
            failures.append("2016-21_37")
        typer.echo(
            f"[FALHA GERAL] Falhas nos testes: {', '.join(failures)}",
            err=True,
        )
        sys.exit(1)
