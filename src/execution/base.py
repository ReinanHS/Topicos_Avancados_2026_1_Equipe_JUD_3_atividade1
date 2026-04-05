import json
import time
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

from src.prompts.renderer import PromptRenderer


class ExecutionManager(ABC):
    """
    Gerenciador base responsável por orquestrar o processo de inferência.

    Fornece o pipeline padrão:
      process_question → classify_difficulty → define_basic_legislation → process_full_question
    """

    def __init__(self, dataset_loader, storage, ollama_client):
        self.dataset_loader = dataset_loader
        self.storage = storage
        self.ollama_client = ollama_client
        self.prompt_renderer = PromptRenderer()

    @property
    @abstractmethod
    def dataset_name(self) -> str:
        """Nome do dataset gerenciado por esta implementação."""
        ...

    @abstractmethod
    def get_questions(self, limit: int = None) -> List[Dict[str, Any]]:
        """Carrega as questões do dataset e aplica o limite caso exista."""
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

    def classify_difficulty(self, q: Dict[str, Any], model: str) -> Dict[str, Any]:
        """
        Classifica o nível de dificuldade da questão usando o template de curador.
        """
        prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        template_path = (
            prompts_dir / "curador" / "difficulty-level" / "user_template.minijinja"
        )

        context = self._build_context_for_curador(q)

        if not template_path.exists():
            return {**q, "error": f"Template não encontrado em {template_path}"}

        user_prompt = self.prompt_renderer.render_from_path(template_path, context)

        system_prompt = (
            "Você é um curador jurídico especializado em questões do Exame da OAB."
        )

        try:
            response = self.ollama_client.generate_response(
                model, system_prompt, user_prompt
            )
        except Exception as e:
            response = f"ERRO: {e}"

        q_result = q.copy()
        q_result["ollama_response"] = response
        q_result["model_used"] = model
        q_result["task"] = "difficulty-level"

        try:
            resp_str_clean = response.replace("```json", "").replace("```", "").strip()
            resp_json = json.loads(resp_str_clean)
            q_result["dificuldade"] = resp_json.get("dificuldade")
        except Exception:
            pass

        return q_result

    def define_basic_legislation(self, q: Dict[str, Any], model: str) -> Dict[str, Any]:
        """
        Identifica a legislação base que fundamenta a questão
        usando o template de curador.
        """
        prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        template_path = (
            prompts_dir / "curador" / "basic-legislation" / "user_template.minijinja"
        )

        context = self._build_context_for_curador(q)

        if not template_path.exists():
            return {**q, "error": f"Template não encontrado em {template_path}"}

        user_prompt = self.prompt_renderer.render_from_path(template_path, context)

        system_prompt = (
            "Você é um curador jurídico especializado em questões do Exame da OAB."
        )

        try:
            response = self.ollama_client.generate_response(
                model, system_prompt, user_prompt
            )
        except Exception as e:
            response = f"ERRO: {e}"

        q_result = q.copy()
        q_result["ollama_response"] = response
        q_result["model_used"] = model
        q_result["task"] = "basic-legislation"
        q_result["user_prompt"] = user_prompt
        q_result["system_prompt"] = system_prompt

        try:
            resp_str_clean = response.replace("```json", "").replace("```", "").strip()
            resp_json = json.loads(resp_str_clean)
            q_result["legislacao_base"] = resp_json.get("legislacao_base")
        except Exception:
            pass

        return q_result

    def process_full_question(self, q: Dict[str, Any], model: str) -> Dict[str, Any]:
        """
        Executa sequencialmente a inferência da questão, a classificação
        de dificuldade e a identificação da legislação base.
        """
        q_result = self.process_question(q, model)
        difficulty_result = self.classify_difficulty(q, model)
        legislation_result = self.define_basic_legislation(q, model)

        final_answer = {
            "question_id": q.get("question_id", q.get("id", "")),
            "answer_id": uuid.uuid4().hex,
            "model_id": model,
            "choices": self._format_choices_for_final_answer(q_result),
            "additional_information": {
                "difficulty_question": difficulty_result.get("dificuldade"),
                "basic_legislation": legislation_result.get("legislacao_base"),
            },
            "tstamp": time.time(),
        }

        if "error" in difficulty_result and difficulty_result["error"]:
            final_answer["additional_information"]["dificuldade_error"] = (
                difficulty_result["error"]
            )

        if "error" in legislation_result and legislation_result["error"]:
            final_answer["additional_information"]["legislacao_error"] = (
                legislation_result["error"]
            )

        return final_answer

    def save_results(self, results: List[Dict[str, Any]], model: str) -> Path:
        """Salva os resultados consolidados na subpasta definida para o cache."""
        sub_dir = f"results/{self.dataset_name}/model_answer"
        filename = model.replace(":", "-")

        output_path = self.storage.save_data(
            results, filename, fmt="json", sub_dir=sub_dir
        )
        return output_path
