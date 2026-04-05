import json
from typing import Any, Dict, List

from src.execution.base import ExecutionManager


class OABExamsExecutionManager(ExecutionManager):
    """
    Executor especializado para o dataset oab_exams.

    Utiliza estratégia single-turn: uma única chamada ao LLM por questão,
    com extração de resposta objetiva do JSON retornado.
    """

    @property
    def dataset_name(self) -> str:
        return "oab_exams"

    def get_questions(self, limit: int = None) -> List[Dict[str, Any]]:
        questions = self.dataset_loader.load_questions()
        if limit is not None and limit > 0:
            questions = questions[:limit]
        return questions

    def _build_context_for_curador(self, q: Dict[str, Any]) -> dict:
        context = q.copy()
        statement = q.get("question", "")
        if "choices" in q:
            choices_text = [
                f"{label}) {text}"
                for label, text in zip(q["choices"]["label"], q["choices"]["text"])
            ]
            statement += "\n\nAlgumas alternativas:\n" + "\n".join(choices_text)
        context["statement"] = statement
        context["category"] = q.get("area", "Sem Área")
        context["question_id"] = q.get("id", "")
        return context

    def process_question(self, q: Dict[str, Any], model: str) -> Dict[str, Any]:
        """Estratégia single-turn para oab_exams."""
        q_result = q.copy()
        q_result["model_used"] = model

        system_prompt = self.prompt_renderer.render(
            self.dataset_name, "system_template.minijinja", q
        )
        if not system_prompt:
            system_prompt = q.get(
                "system",
                "Você é um assistente prestativo especialista em direito brasileiro.",
            )

        user_prompt = self.prompt_renderer.render(
            self.dataset_name, "user_template.minijinja", q
        )

        if not user_prompt:
            user_prompt = q.get("statement", q.get("question", ""))
            if "choices" in q:
                choices_text = [
                    f"{label}) {text}"
                    for label, text in zip(q["choices"]["label"], q["choices"]["text"])
                ]
                user_prompt += "\n" + "\n".join(choices_text)

        try:
            response = self.ollama_client.generate_response(
                model, system_prompt, user_prompt
            )
        except Exception as e:
            response = f"ERRO: {e}"

        q_result["ollama_response"] = response

        resp_str_clean = response.replace("```json", "").replace("```", "").strip()
        try:
            resp_json = json.loads(resp_str_clean)
            q_result["objective_answer"] = resp_json.get("resposta_objetiva", "")
        except Exception:
            q_result["objective_answer"] = ""

        return q_result

    def _format_choices_for_final_answer(self, q_result: Dict[str, Any]) -> List[Any]:
        return [{"objective_answer": q_result.get("objective_answer", "")}]
