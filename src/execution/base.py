import json
import re
import time
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.prompts.renderer import PromptRenderer

_DEFAULT_SYSTEM_PROMPT = (
    "Você é um assistente prestativo especialista em direito brasileiro."
)

_INSTITUTE_DEFINITIONS = {
    "erro": "falsa percepção espontânea da realidade.",
    "dolo": "induzimento malicioso ao erro por parte de outrem.",
    "coacao": "ameaça grave e iminente que infunde temor.",
    "estado de perigo": "emergência/grave dano e obrigação excessivamente onerosa.",
    "lesao": "obrigação desproporcional por necessidade premente ou inexperiência.",
    "fraude": "alienação de bens para frustrar execução ou cobrança.",
    "simulacao": "declaração enganosa para aparentar negócio inexistente ou diferente.",
    "nulidade": "invalidade absoluta e insanável por infração de ordem pública.",
    "anulabilidade": "invalidade relativa, sanável ou confirmável pelas partes.",
    "prescricao": "extinção da pretensão de cobrar/exigir um direito pelo decurso do tempo.",
    "decadencia": "extinção do próprio direito potestativo por falta de exercício no prazo.",
    "incapacidade absoluta": "invalidade absoluta do ato (ex: menores de 16 anos).",
    "incapacidade relativa": "invalidade relativa (ex: maiores de 16 e menores de 18 ou causa transitória).",
    "causa transitoria": "impedimento temporário de exprimir a vontade, gerando incapacidade relativa.",
}


class ExecutionManager(ABC):
    """
    Gerenciador base responsável por orquestrar o processo de inferência.
    """

    def __init__(self, dataset_loader, storage, ollama_client):
        self.dataset_loader = dataset_loader
        self.storage = storage
        self.ollama_client = ollama_client
        self.prompt_renderer = PromptRenderer()
        self.use_rag = False
        self._rag_db = None
        self.top_k = 3

    def set_top_k(self, top_k: int) -> None:
        """Define o valor de top_k para a busca RAG."""
        self.top_k = top_k

    def set_rag(self, use_rag: bool) -> None:
        """Habilita ou desabilita o uso do RAG."""
        self.use_rag = use_rag
        if use_rag and self._rag_db is None:
            from src.rag.database import LegislationVectorDB
            from src.rag.embeddings import OllamaEmbeddingProvider

            provider = OllamaEmbeddingProvider(model_name="qwen3-embedding:8b")
            self._rag_db = LegislationVectorDB(
                db_path=".reinan_cache/chromadb",
                collection_name="legislacao",
                embedding_provider=provider,
            )

    def _resolve_retrieval_notes(self, meta: dict) -> str:
        """Resolve a descrição interpretativa (Uso) a partir dos metadados ricos."""
        retrieval_notes = meta.get("retrieval_notes", "")
        if retrieval_notes:
            return retrieval_notes

        institute = meta.get("canonical_institute", "")
        category = meta.get("legal_category", "")
        effect = meta.get("legal_effect", "")
        if not institute:
            return f"dispositivo legal relativo a {meta.get('legal_area', 'Direito')}."

        notes = f"define o instituto '{institute}'"
        if category:
            notes += f" no âmbito de '{category}'"
        if effect:
            notes += f", com o efeito jurídico de '{effect}'"
        return notes

    def _process_single_rag_result(
        self, idx: int, res: dict, confidence_level: str
    ) -> tuple[dict, str]:
        """Processa um único resultado RAG e retorna as informações estruturadas e formatadas."""
        meta = res.get("metadata", {})
        law_title = meta.get("law_title", "Desconhecida")
        file_name = meta.get("file_name", "")
        article = meta.get("article", "Desconhecido")
        score = res.get("score", 0.0)
        raw_text = meta.get("raw_text", res.get("text", ""))

        law_str = f"{law_title}"
        if file_name:
            law_str += f" ({file_name})"

        info = {
            "Lei": law_str,
            "Artigo": article,
            "Score": round(score, 4),
            "Score Vetorial Base": round(res.get("vector_score", 0.0), 4),
            "Score Lexical Base": round(res.get("lexical_score", 0.0), 4),
            "Score Hibrido Base": round(res.get("base_score", 0.0), 4),
            "Boost": round(res.get("boost", 0.0), 4),
            "Penalidade": round(res.get("penalty", 0.0), 4),
            "Justificativa": res.get("rerank_reason", ""),
            "Confianca": confidence_level,
        }

        retrieval_notes = self._resolve_retrieval_notes(meta)

        # Garante a formatação do texto oficial sem poluição interpretativa
        indented_text = "\n".join(f"   {line}" for line in raw_text.strip().split("\n"))

        context_part = (
            f"{idx + 1}. {law_title} — {article}\n"
            f"   Uso: {retrieval_notes}\n"
            f"   Texto:\n"
            f"{indented_text}"
        )
        return info, context_part

    def _query_rag(self, q: Any, k: int, model: Optional[str]) -> List[dict]:
        """Consulta o banco vetorial RAG."""
        try:
            return (
                self._rag_db.query(q, top_k=k, top_k_retrieval=100, model=model) or []
            )
        except Exception as e:
            print(f"[RAG] Erro ao consultar banco vetorial: {e}")
            return []

    def _apply_confidence_threshold(
        self, results: List[dict], k: int
    ) -> tuple[str, List[dict], Optional[dict]]:
        """Aplica a avaliação de confiança para filtrar os resultados."""
        if not results:
            return "high", [], None

        confidence = results[0].get("confidence", {})
        confidence_level = confidence.get("level", "high")
        suggested_k = confidence.get("suggested_k", k)
        effective_k = min(len(results), suggested_k)

        if effective_k <= 0:
            print(
                f"[RAG] Confiança baixa ({confidence.get('reason', '')}). Fallback sem RAG."
            )
            return confidence_level, [], {"confidence": confidence}

        return confidence_level, results[:effective_k], None

    def _collect_single_meta_concepts(self, res: dict, concepts: set[str]) -> None:
        """Extrai institutos e distinções dos metadados de um único resultado RAG."""
        meta = res.get("metadata", {})
        inst = meta.get("canonical_institute")
        if inst:
            concepts.add(inst.strip().lower())
        dist = meta.get("distinguish_from", [])
        if isinstance(dist, list):
            for d in dist:
                if d:
                    concepts.add(d.strip().lower())

    def _collect_meta_concepts(self, results: List[dict]) -> set[str]:
        """Extrai institutos e distinções dos metadados dos resultados RAG."""
        concepts = set()
        for res in results:
            self._collect_single_meta_concepts(res, concepts)
        return concepts

    def _collect_choice_concepts(self, q: Any) -> set[str]:
        """Extrai conceitos das alternativas da questão."""
        concepts = set()
        if not isinstance(q, dict):
            return concepts

        from src.rag.chunker import strip_accents

        choices = q.get("choices", {})
        if not (choices and "text" in choices):
            return concepts

        for choice_text in choices["text"]:
            choice_clean = strip_accents(choice_text).lower().strip(". ")
            for key in _INSTITUTE_DEFINITIONS:
                if key in choice_clean:
                    concepts.add(key)
        return concepts

    def _collect_distinct_concepts(self, results: List[dict], q: Any) -> set[str]:
        """Coleta conceitos jurídicos dos metadados e das alternativas da questão."""
        meta_concepts = self._collect_meta_concepts(results)
        choice_concepts = self._collect_choice_concepts(q)
        return meta_concepts.union(choice_concepts)

    def _compile_alerts(
        self, q: Any, distinct_concepts: set[str], confidence_level: str
    ) -> str:
        """Gera alertas de distinção jurídicas estáticos e dinâmicos e de nível de confiança."""
        dynamic_alerts = []
        for concept in sorted(distinct_concepts):
            if concept in _INSTITUTE_DEFINITIONS:
                dynamic_alerts.append(
                    f"{concept.capitalize()} envolve {_INSTITUTE_DEFINITIONS[concept]}"
                )

        distinction_alerts = self._build_distinction_alerts(q)

        # Combina alertas estáticos e dinâmicos sem duplicidades
        for alert in dynamic_alerts:
            concept_name = alert.split(" ")[0].lower()
            if not any(
                concept_name in static_alert.lower()
                for static_alert in distinction_alerts
            ):
                distinction_alerts.append(alert)

        alert_parts = []
        if distinction_alerts:
            alert_parts.append(
                "\n\n[ALERTA DE DISTINÇÃO]\n"
                + "\n".join(f"- {alert}" for alert in distinction_alerts)
            )

        if confidence_level != "high":
            alert_parts.append(
                f"\n\n[ALERTA] Confiança da recuperação: {confidence_level}. Use os artigos com cautela."
            )

        return "".join(alert_parts)

    def get_rag_context_and_info(
        self, q: Any, top_k: Optional[int] = None, model: Optional[str] = None
    ) -> tuple[str, list]:
        """
        Realiza busca híbrida no banco vetorial e retorna contexto textual compacto
        e info estruturada. Aplica avaliação de confiança para ajustar o volume
        de contexto enviado ao modelo.
        """
        if not self.use_rag or not self._rag_db:
            return "", []

        k = top_k if top_k is not None else self.top_k
        results = self._query_rag(q, k, model)
        if not results:
            return "", []

        confidence_level, results, fallback_res = self._apply_confidence_threshold(
            results, k
        )
        if fallback_res is not None:
            return "", [fallback_res]

        rag_info = []
        context_parts = []
        for idx, res in enumerate(results):
            info, context_part = self._process_single_rag_result(
                idx, res, confidence_level
            )
            rag_info.append(info)
            context_parts.append(context_part)

        context_str = "[LEGISLAÇÃO RELEVANTE]\n" + "\n\n".join(context_parts)
        distinct_concepts = self._collect_distinct_concepts(results, q)
        context_str += self._compile_alerts(q, distinct_concepts, confidence_level)

        return context_str, rag_info

    @staticmethod
    def _build_distinction_alerts(q: Any) -> list:
        """
        Gera alertas curtos de distinção jurídica com base nos pares de conceitos
        que as alternativas distinguem. Ajuda o modelo pequeno a não confundir.
        """
        if not isinstance(q, dict):
            return []

        try:
            from src.rag.database import LegislationVectorDB

            pairs = LegislationVectorDB._extract_distinction_terms(q)
        except Exception:
            return []

        if not pairs:
            return []

        # Mapeamento de explicações para pares comuns
        pair_explanations = {
            (
                "nulidade",
                "anulacao",
            ): "Nulidade = invalidade absoluta (Art. 166). Anulação = invalidade relativa (Art. 171). Se o fundamento apontar para 'anulável', NÃO escolha 'nulidade'.",
            (
                "nulidade",
                "anulabilidade",
            ): "Nulidade = ato nulo de pleno direito. Anulabilidade = ato anulável por vício sanável.",
            (
                "nulo",
                "anulavel",
            ): "Ato nulo não produz efeitos. Ato anulável produz efeitos até ser anulado.",
            (
                "prescricao",
                "decadencia",
            ): "Prescrição extingue a pretensão (direito subjetivo). Decadência extingue o próprio direito (potestativo).",
            (
                "incapacidade absoluta",
                "incapacidade relativa",
            ): "Absolutamente incapaz = menores de 16 anos. Relativamente incapaz = maiores de 16 e menores de 18 ou com causa transitória.",
            (
                "absolutamente incapaz",
                "relativamente incapaz",
            ): "Absolutamente incapaz → ato NULO. Relativamente incapaz → ato ANULÁVEL.",
            (
                "erro",
                "dolo",
            ): "Erro = falsa percepção espontânea. Dolo = indução em erro pela outra parte.",
            (
                "coacao",
                "estado de perigo",
            ): "Coação = ameaça. Estado de perigo = necessidade de salvar a si ou parente.",
            (
                "causa transitoria",
                "enfermidade",
            ): "Causa transitória (Art. 4.º, III) = incapacidade relativa → anulação. Enfermidade/deficiência mental não é mais causa automática de incapacidade (Lei 13.146/2015).",
            (
                "causa transitoria",
                "deficiencia mental",
            ): "Causa transitória = impedimento temporário de exprimir vontade → incapacidade relativa. Deficiência mental = não afeta automaticamente a capacidade (Lei 13.146/2015).",
            (
                "apelacao",
                "agravo",
            ): "Apelação = recurso contra sentença. Agravo de instrumento = recurso contra decisão interlocutória.",
            (
                "rescisao",
                "resolucao",
            ): "Rescisão = término de contrato por causa superveniente. Resolução = término por inadimplemento.",
            (
                "dano moral",
                "dano material",
            ): "Dano moral = lesão a direito de personalidade. Dano material = prejuízo patrimonial efetivo.",
        }

        alerts = []
        for pair in pairs:
            # Tenta com a chave direta e inversa
            explanation = pair_explanations.get(pair) or pair_explanations.get(
                (pair[1], pair[0])
            )
            if explanation:
                alerts.append(explanation)
            else:
                alerts.append(f"Atenção à diferença entre '{pair[0]}' e '{pair[1]}'.")

        return alerts

    @property
    @abstractmethod
    def dataset_name(self) -> str:
        """Nome do dataset gerenciado por esta implementação."""
        ...

    @abstractmethod
    def process_question(self, q: Dict[str, Any], model: str) -> Dict[str, Any]:
        """Recebe uma questão crua, formata o prompt e extrai a resposta do LLM."""
        ...

    @abstractmethod
    def _build_context_for_curador(self, q: Dict[str, Any]) -> dict:
        """Constrói o contexto para ser usado nos templates do curador."""
        ...

    @abstractmethod
    def _format_choices_for_final_answer(self, q_result: Dict[str, Any]) -> List[Any]:
        """Formata as escolhas para a estrutura de resposta final."""
        ...

    def get_questions(
        self, limit: int = None, question_ids: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Carrega as questões do dataset e aplica o limite caso exista.
        """
        questions = self.dataset_loader.load_questions()
        if question_ids:
            questions = [
                q
                for q in questions
                if str(q.get("question_id", q.get("id", ""))) in question_ids
            ]
        if limit is not None and limit > 0:
            questions = questions[:limit]
        return questions

    def _resolve_system_prompt(self, q: Dict[str, Any]) -> str:
        """
        Renderiza o template de sistema para o dataset atual.
        """
        rendered = self.prompt_renderer.render(
            self.dataset_name, "system_template.minijinja", q
        )
        if rendered:
            return rendered
        return q.get("system", _DEFAULT_SYSTEM_PROMPT)

    def _parse_json_response(
        self, response: str, key: str, default: Any = "Inconclusivo"
    ) -> Any:
        """
        Limpa marcadores de code-fence e parseia a resposta JSON do LLM.
        Inclui fallback com regex para lidar com JSONs malformados.
        """
        cleaned = response.replace("```json", "").replace("```", "").strip()
        cleaned = cleaned.replace("“", '"').replace("”", '"')
        try:
            data = json.loads(cleaned, strict=False)
            if not isinstance(data, dict):
                raise ValueError("Parsed JSON is not a dictionary")
            return data.get(key, default)
        except (json.JSONDecodeError, ValueError):
            pattern = rf'"{re.escape(key)}"\s*:\s*"([^"]*)"'
            match = re.search(pattern, cleaned)
            if match:
                try:
                    return json.loads('"' + match.group(1) + '"', strict=False)
                except Exception:
                    return match.group(1)

            pattern_multiline = (
                rf'"{re.escape(key)}"\s*:\s*"(.*?)"(?:\s*,\s*"|\s*\}}|\s*$)'
            )
            match = re.search(pattern_multiline, cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads('"' + match.group(1) + '"', strict=False)
                except Exception:
                    return match.group(1)

            return default

    @staticmethod
    def _attach_errors_to_answer(
        additional_info: dict, error_mappings: List[tuple]
    ) -> None:
        """
        Anexa erros de curadoria ao dicionário de informações adicionais.
        """
        for result, error_key in error_mappings:
            error_value = result.get("error")
            if error_value:
                additional_info[error_key] = error_value

    def _execute_curador_task(
        self, q: Dict[str, Any], model: str, task_dir_name: str, result_key: str
    ) -> Dict[str, Any]:
        """
        Executa uma tarefa genérica de curadoria chamando o LLM com templates específicos.
        """
        prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        curador_dir = prompts_dir / "curador" / task_dir_name
        user_template_path = curador_dir / "user_template.minijinja"
        system_template_path = curador_dir / "system_template.minijinja"

        context = self._build_context_for_curador(q)
        user_prompt = self.prompt_renderer.render_from_path(user_template_path, context)
        system_prompt = self.prompt_renderer.render_from_path(system_template_path, {})

        try:
            response = self.ollama_client.generate_response(
                model, system_prompt, user_prompt
            )
        except Exception as e:
            return {**q, "error": f"ERRO: {e}"}

        q_result = q.copy()
        q_result[result_key] = self._parse_json_response(response, result_key)
        return q_result

    def classify_difficulty(self, q: Dict[str, Any], model: str) -> Dict[str, Any]:
        """Classifica o nível de dificuldade da questão usando os templates de curador."""
        return self._execute_curador_task(
            q, model, "classify_difficulty", "difficulty_question"
        )

    def define_basic_legislation(self, q: Dict[str, Any], model: str) -> Dict[str, Any]:
        """
        Identifica a legislação base que fundamenta a questão
        usando os templates de curador.
        """
        return self._execute_curador_task(
            q, model, "basic_legislation", "basic_legislation"
        )

    def define_area_expertise(self, q: Dict[str, Any], model: str) -> Dict[str, Any]:
        """
        Identifica a área de expertise que fundamenta a questão
        usando os templates de curador.
        """
        return self._execute_curador_task(q, model, "area_expertise", "area_expertise")

    def process_full_question(self, q: Dict[str, Any], model: str) -> Dict[str, Any]:
        """
        Executa sequencialmente a inferência da questão, a classificação
        de dificuldade, a identificação da legislação base e da área de expertise.
        """
        q_result = self.process_question(q, model)
        difficulty_result = self.classify_difficulty(q, model)
        legislation_result = self.define_basic_legislation(q, model)
        area_expertise_result = self.define_area_expertise(q, model)

        additional_info = {
            "difficulty_question": difficulty_result.get("difficulty_question"),
            "basic_legislation": legislation_result.get("basic_legislation"),
            "area_expertise": area_expertise_result.get("area_expertise"),
        }

        self._attach_errors_to_answer(
            additional_info,
            [
                (difficulty_result, "dificuldade_error"),
                (legislation_result, "legislacao_error"),
            ],
        )

        ans = {
            "question_id": q.get("question_id", q.get("id", "")),
            "answer_id": uuid.uuid4().hex,
            "model_id": model,
            "choices": self._format_choices_for_final_answer(q_result),
            "additional_information": additional_info,
            "tstamp": time.time(),
        }
        if "rag_info" in q_result:
            ans["rag_info"] = q_result["rag_info"]
        return ans

    def save_results(
        self,
        results: List[Dict[str, Any]],
        model: str,
        filename_suffix: str = "",
        append: bool = False,
    ) -> Path:
        """Salva os resultados consolidados na subpasta definida para o cache."""
        suffix = "rag" if self.use_rag else "default"
        sub_dir = f"results/{self.dataset_name}/model_answer/{suffix}"
        filename = model.replace(":", "-") + filename_suffix

        if append:
            try:
                existing_data = self.storage.load_data(
                    filename, fmt="json", sub_dir=sub_dir
                )
                if isinstance(existing_data, list):
                    results = existing_data + results
            except FileNotFoundError:
                pass

        output_path = self.storage.save_data(
            results, filename, fmt="json", sub_dir=sub_dir
        )
        return output_path
