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

        try:
            resp_str_clean = response.replace("```json", "").replace("```", "").strip()
            resp_json = json.loads(resp_str_clean)
            value = resp_json.get(result_key)
            q_result[result_key] = value
        except Exception:
            q_result[result_key] = "Inconclusivo"

        return q_result

    def classify_difficulty(self, q: Dict[str, Any], model: str) -> Dict[str, Any]:
        """
        Classifica o nível de dificuldade da questão usando os templates de curador.
        """
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
        de dificuldade e a identificação da legislação base.
        """
        q_result = self.process_question(q, model)
        difficulty_result = self.classify_difficulty(q, model)
        legislation_result = self.define_basic_legislation(q, model)
        area_expertise_result = self.define_area_expertise(q, model)

        final_answer = {
            "question_id": q.get("question_id", q.get("id", "")),
            "answer_id": uuid.uuid4().hex,
            "model_id": model,
            "choices": self._format_choices_for_final_answer(q_result),
            "additional_information": {
                "difficulty_question": difficulty_result.get("difficulty_question"),
                "basic_legislation": legislation_result.get("basic_legislation"),
                "area_expertise": area_expertise_result.get("area_expertise"),
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
