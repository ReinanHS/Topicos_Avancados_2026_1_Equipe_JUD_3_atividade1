from pathlib import Path
from typing import List, Dict, Any, Optional
import typer
from src.rag.chunker import LegislationChunker


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
        typer.echo(f"    Score (Distância): {res['score']:.4f}")

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
    """Orquestra as consultas semânticas no ChromaDB RAG."""
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

    default_queries = [
        "Quais são os crimes de abuso de autoridade?",
        "Quais são os direitos básicos do consumidor?",
        "O que caracteriza improbidade administrativa e enriquecimento ilícito?",
    ]

    queries_to_run = [query_text] if query_text else default_queries

    for q in queries_to_run:
        typer.echo(f"\nConsulta: '{q}'")
        results = db.query(q, top_k=top_k)

        # Exibe os resultados
        _print_query_results(results)
        typer.echo("-" * 60)
