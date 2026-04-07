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

    def _build_context_for_curador(self, q: Dict[str, Any]) -> dict:
        """Constrói o contexto para os templates de curadoria do oab_exams."""
        context = q.copy()
        statement = q.get("question", "")

        if "choices" in q:
            statement += "\n\nAlgumas alternativas:\n" + self._format_choices_as_text(
                q["choices"]
            )

        context["statement"] = statement
        context["category"] = q.get("area", "Sem Área")
        context["question_id"] = q.get("id", "")
        return context

    def process_question(self, q: Dict[str, Any], model: str) -> Dict[str, Any]:
        """
        Estratégia single-turn para oab_exams.

        Renderiza o prompt, envia ao LLM e extrai a resposta objetiva
        (letra da alternativa) do JSON retornado.
        """
        q_result = q.copy()
        q_result["model_used"] = model

        system_prompt = self._resolve_system_prompt(q)
        user_prompt = self._build_user_prompt(q)

        try:
            response = self.ollama_client.generate_response(
                model, system_prompt, user_prompt
            )
        except Exception as e:
            response = f"ERRO: {e}"

        q_result["ollama_response"] = response
        q_result["objective_answer"] = self._parse_json_response(
            response, "resposta_objetiva", default=""
        )

        return q_result

    def _format_choices_for_final_answer(self, q_result: Dict[str, Any]) -> List[Any]:
        """Retorna a resposta objetiva encapsulada para a estrutura final."""
        return [{"objective_answer": q_result.get("objective_answer", "")}]

    def _build_user_prompt(self, q: Dict[str, Any]) -> str:
        """
        Renderiza o template de usuário ou constrói um fallback
        a partir dos campos da questão.
        """
        rendered = self.prompt_renderer.render(
            self.dataset_name, "user_template.minijinja", q
        )
        if rendered:
            return rendered

        prompt = q.get("statement", q.get("question", ""))
        if "choices" in q:
            prompt += "\n" + self._format_choices_as_text(q["choices"])
        return prompt

    @staticmethod
    def _format_choices_as_text(choices: Dict[str, Any]) -> str:
        """
        Formata as alternativas de múltipla escolha em texto legível.
        """
        return "\n".join(
            f"{label}) {text}" for label, text in zip(choices["label"], choices["text"])
        )
