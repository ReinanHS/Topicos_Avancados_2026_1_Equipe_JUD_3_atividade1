import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.llm.ollama_client import OllamaClient
from src.rag.chunker import LegislationChunker

# Expected schema fields and their default types/values
EXPECTED_FIELDS = {
    "canonical_institute": "",
    "legal_category": "",
    "article_role": "",
    "legal_effect": "",
    "fact_triggers": [],
    "synonyms": [],
    "related_terms": [],
    "distinguish_from": [],
    "synthetic_queries": [],
    "is_generic_list_article": False,
    "is_deadline_article": False,
    "is_definition_article": False,
    "is_exception_article": False,
    "target_legal_area": "",
    "retrieval_notes": "",
}


def _strip_markdown_and_normalize(text: str) -> str:
    """Strip markdown json code block indicators and normalize double quotes."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
        cleaned = re.sub(r"\n```$", "", cleaned)
        cleaned = cleaned.strip()
    return cleaned.replace("“", '"').replace("”", '"')


def _fallback_regex_json(text: str) -> Optional[dict]:
    """Fallback regex extraction of the first JSON block { ... }."""
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            data = json.loads(match.group(0), strict=False)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return None


def clean_and_parse_json(text: str) -> Optional[dict]:
    """Clean markdown code blocks and parse JSON string."""
    cleaned = _strip_markdown_and_normalize(text)
    try:
        data = json.loads(cleaned, strict=False)
        if isinstance(data, dict):
            return data
    except Exception:
        return _fallback_regex_json(cleaned)
    return None


def _normalize_bool(val: Any) -> bool:
    """Normalize value to boolean."""
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ("true", "1", "yes")
    return bool(val)


def _normalize_list(val: Any) -> List[str]:
    """Normalize value to list of strings."""
    if isinstance(val, list):
        return [str(x).strip() for x in val if x]
    if isinstance(val, str):
        return [x.strip() for x in val.split(",") if x.strip()]
    return []


def _normalize_field(val: Any, default_val: Any) -> Any:
    """Normalize a single metadata field value according to the default value's type."""
    if val is None:
        return default_val

    if isinstance(default_val, bool):
        return _normalize_bool(val)

    if isinstance(default_val, list):
        return _normalize_list(val)

    return str(val).strip()


def validate_and_normalize_metadata(data: dict) -> dict:
    """Ensure all required fields exist and conform to their expected types."""
    return {
        key: _normalize_field(data.get(key), default_val)
        for key, default_val in EXPECTED_FIELDS.items()
    }


def build_system_prompt() -> str:
    """Build the system prompt for metadata enrichment."""
    return (
        "Você é um especialista em RAG jurídico e análise de legislação brasileira.\n"
        "Sua tarefa é analisar o texto de um artigo de lei e seu contexto estrutural e gerar metadados de recuperação em formato JSON.\n"
        "Regras críticas:\n"
        "1. Analise apenas o artigo fornecido. Não tente responder a questões ou criar gabaritos.\n"
        "2. Não cite IDs de questões nem invente números de artigos.\n"
        "3. Gere apenas metadados gerais de recuperação úteis para conectar fatos narrados a este artigo.\n"
        "4. Retorne APENAS um objeto JSON válido, sem cercas de código (```json), sem explicações ou textos adicionais fora do JSON.\n"
        "5. Garanta que o JSON contenha exatamente as seguintes chaves, respeitando os tipos esperados:\n"
        "   - 'canonical_institute' (string): Instituto jurídico principal do artigo.\n"
        "   - 'legal_category' (string): Categoria jurídica ampla (ex: defeitos do negócio jurídico, prescrição, recursos).\n"
        "   - 'article_role' (string): Papel do artigo (ex: 'definicao_instituto', 'regra_geral', 'excecao', 'prazo', 'procedimento', 'competencia').\n"
        "   - 'legal_effect' (string): Efeito jurídico principal (ex: 'anulabilidade', 'nulidade', 'responsabilização').\n"
        "   - 'fact_triggers' (lista de strings): Situações fáticas concretas que costumam apontar para esse artigo.\n"
        "   - 'synonyms' (lista de strings): Sinônimos e expressões equivalentes.\n"
        "   - 'related_terms' (lista de strings): Termos jurídicos correlatos.\n"
        "   - 'distinguish_from' (lista de strings): Institutos parecidos dos quais este deve ser diferenciados.\n"
        "   - 'synthetic_queries' (lista de strings): Consultas hipotéticas em linguagem natural para buscar este artigo.\n"
        "   - 'is_generic_list_article' (boolean): true se o artigo apenas lista vários institutos sem defini-los profundamente.\n"
        "   - 'is_deadline_article' (boolean): true se tratar principalmente de prazo.\n"
        "   - 'is_definition_article' (boolean): true se o artigo definir um instituto.\n"
        "   - 'is_exception_article' (boolean): true se trouxer uma exceção.\n"
        "   - 'target_legal_area' (string): Ramo do Direito mais provável.\n"
        "   - 'retrieval_notes' (string): Frase curta explicando quando este artigo deve ser priorizado."
    )


def enrich_single_article(
    client: OllamaClient, model: str, chunk: Dict[str, Any]
) -> Optional[dict]:
    """Call Ollama LLM to generate enriched metadata for a single article chunk."""
    system_prompt = build_system_prompt()
    user_prompt = (
        f"Lei: {chunk['law_title']}\n"
        f"Caminho estrutural: {chunk.get('heading_path', '')}\n"
        f"Artigo: {chunk['article']}\n"
        f"Texto do artigo:\n{chunk['raw_text']}\n\n"
        f"Gere o JSON de metadados enriquecidos para o artigo acima:"
    )

    for attempt in range(1, 4):
        try:
            response = client.generate_response(model, system_prompt, user_prompt)
            data = clean_and_parse_json(response)
            if data is not None:
                return validate_and_normalize_metadata(data)
            print(
                f"  [Tentativa {attempt}/3] Falha ao analisar resposta do LLM como JSON para {chunk['article']}."
            )
        except Exception as e:
            print(
                f"  [Tentativa {attempt}/3] Erro ao chamar LLM para {chunk['article']}: {e}"
            )

    return None


def load_existing_cache(cache_path: Path) -> dict:
    """Load existing metadata cache if available."""
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar cache de {cache_path.name}: {e}")
    return {}


def _should_skip_chunk(
    chunk: Dict[str, Any],
    cache_data: dict,
    force: bool,
    article_filter: Optional[str],
) -> bool:
    """Determine if a chunk should be skipped based on filter and cache presence."""
    article_key = chunk["article"]
    if article_filter and article_filter.lower() not in article_key.lower():
        return True
    if article_key in cache_data and not force:
        return True
    return False


def _enrich_and_cache_chunk(
    client: OllamaClient,
    model: str,
    chunk: Dict[str, Any],
    cache_data: dict,
    cache_path: Path,
) -> bool:
    """Enrich a single chunk and update the cache file."""
    article_key = chunk["article"]
    print(f"Enriquecendo {chunk['law_title']} - {article_key}...")
    enriched = enrich_single_article(client, model, chunk)
    if enriched:
        cache_data[article_key] = enriched
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        return True
    return False


def process_file_chunks(
    client: OllamaClient,
    model: str,
    chunks: List[Dict[str, Any]],
    cache_path: Path,
    force: bool,
    limit: Optional[int],
    article_filter: Optional[str],
    enriched_count: int,
) -> int:
    """Process all chunks for a single law file, managing the cache."""
    cache_data = load_existing_cache(cache_path)

    for chunk in chunks:
        # Check limit
        if limit is not None and enriched_count >= limit:
            break

        if _should_skip_chunk(chunk, cache_data, force, article_filter):
            continue

        if _enrich_and_cache_chunk(client, model, chunk, cache_data, cache_path):
            enriched_count += 1

    return enriched_count


def _select_fallback_model(installed_models: List[str]) -> str:
    """Select a fallback model from the installed models list, prioritizing large models."""
    large_fallbacks = [
        m
        for m in installed_models
        if any(sz in m.lower() for sz in ["27b", "32b", "70b", "14b", "8b"])
        and "embed" not in m.lower()
    ]
    if large_fallbacks:
        model = large_fallbacks[0]
        print(f"Selecionando '{model}' como modelo de enriquecimento fallback.")
        return model

    non_embed = [m for m in installed_models if "embed" not in m.lower()]
    if non_embed:
        model = non_embed[0]
        print(f"Selecionando '{model}' como modelo fallback.")
        return model

    model = installed_models[0]
    print(f"Selecionando '{model}' como fallback.")
    return model


def _resolve_enrichment_model(client: OllamaClient, configured_model: str) -> str:
    """Resolve the model to use, falling back to installed large models if needed."""
    try:
        models_response = client.client.list()
        installed_models = [m.model for m in models_response.models]
    except Exception as e:
        print(f"Erro ao listar modelos do Ollama: {e}")
        installed_models = []

    resolved_model = configured_model
    if installed_models:
        model_found = any(configured_model in m for m in installed_models)
        if not model_found:
            print(
                f"Aviso: O modelo configurado '{configured_model}' não está instalado no Ollama local."
            )
            resolved_model = _select_fallback_model(installed_models)
    else:
        print(
            f"Nenhum modelo listado no Ollama. Usando o modelo configurado '{configured_model}'."
        )

    if resolved_model not in client.AVAILABLE_MODELS:
        client.AVAILABLE_MODELS.append(resolved_model)
    return resolved_model


def _get_target_files(
    rag_dir: Path, file_filter: Optional[str]
) -> Optional[List[Path]]:
    """Get list of target HTML files in the legislation directory, applying filter."""
    if not rag_dir.exists():
        print(f"Erro: O diretório de legislação '{rag_dir}' não existe.")
        return None

    html_files = list(rag_dir.glob("*.html"))
    if not html_files:
        print(f"Nenhum arquivo HTML encontrado em '{rag_dir}'.")
        return None

    if file_filter:
        html_files = [f for f in html_files if file_filter.lower() in f.name.lower()]
        if not html_files:
            print(f"Nenhum arquivo HTML corresponde ao filtro '{file_filter}'.")
            return None

    return html_files


def run_enrichment_pipeline(
    model: str = "qwen3.6:27b",
    force: bool = False,
    limit: Optional[int] = None,
    file_filter: Optional[str] = None,
    article_filter: Optional[str] = None,
) -> None:
    """Run the complete metadata enrichment pipeline offline."""
    rag_dir = Path("database/rag")
    enriched_dir = Path("database/enriched_metadata")

    html_files = _get_target_files(rag_dir, file_filter)
    if not html_files:
        return

    client = OllamaClient()
    resolved_model = _resolve_enrichment_model(client, model)

    chunker = LegislationChunker()
    enriched_count = 0

    print(
        f"=== Iniciando Enriquecimento Offline via Ollama (Modelo: {resolved_model}) ==="
    )

    for file_path in html_files:
        if limit is not None and enriched_count >= limit:
            break

        print(f"\nFatiando e processando: {file_path.name}")
        chunks = chunker.chunk_file(file_path)
        if not chunks:
            continue

        cache_path = enriched_dir / f"{file_path.stem}.json"
        enriched_count = process_file_chunks(
            client,
            resolved_model,
            chunks,
            cache_path,
            force,
            limit,
            article_filter,
            enriched_count,
        )

    print(
        f"\n=== Enriquecimento Concluído! Total de novos artigos enriquecidos: {enriched_count} ==="
    )
