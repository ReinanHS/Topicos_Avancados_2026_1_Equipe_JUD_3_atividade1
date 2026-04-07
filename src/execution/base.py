import json
import time
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

from src.prompts.renderer import PromptRenderer

_DEFAULT_SYSTEM_PROMPT = (
    "Você é um assistente prestativo especialista em direito brasileiro."
)


class ExecutionManager(ABC):
    """
    Gerenciador base responsável por orquestrar o processo de inferência.
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

    def get_questions(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Carrega as questões do dataset e aplica o limite caso exista.
        """
        questions = self.dataset_loader.load_questions()
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
        """
        cleaned = response.replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(cleaned)
            return data.get(key, default)
        except (json.JSONDecodeError, ValueError):
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

        return {
            "question_id": q.get("question_id", q.get("id", "")),
            "answer_id": uuid.uuid4().hex,
            "model_id": model,
            "choices": self._format_choices_for_final_answer(q_result),
            "additional_information": additional_info,
            "tstamp": time.time(),
        }

    def save_results(self, results: List[Dict[str, Any]], model: str) -> Path:
        """Salva os resultados consolidados na subpasta definida para o cache."""
        sub_dir = f"results/{self.dataset_name}/model_answer"
        filename = model.replace(":", "-")

        output_path = self.storage.save_data(
            results, filename, fmt="json", sub_dir=sub_dir
        )
        return output_path
