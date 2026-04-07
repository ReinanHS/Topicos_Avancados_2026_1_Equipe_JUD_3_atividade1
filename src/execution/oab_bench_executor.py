from typing import Any, Dict, List

from src.execution.base import ExecutionManager


class OABBenchExecutionManager(ExecutionManager):
    """
    Executor especializado para o dataset oab_bench.

    Utiliza estratégia multi-turn: itera por cada turno da questão,
    mantendo o histórico de mensagens entre as chamadas ao LLM.
    """

    @property
    def dataset_name(self) -> str:
        return "oab_bench"

    def _build_context_for_curador(self, q: Dict[str, Any]) -> dict:
        """Constrói o contexto para os templates de curadoria do oab_bench."""
        context = q.copy()
        context["statement"] = q.get("statement", "")
        context["category"] = q.get("category", "")
        context["question_id"] = q.get("question_id", "")
        context["turns"] = q.get("turns", [])
        return context

    def process_question(self, q: Dict[str, Any], model: str) -> Dict[str, Any]:
        """
        Estratégia multi-turn para oab_bench.

        Itera por cada turno da questão, enviando mensagens em sequência
        e acumulando o histórico de conversação.
        """
        q_result = q.copy()
        q_result["model_used"] = model

        system_prompt = self._resolve_system_prompt(q)
        turns = list(q.get("turns", [])) or [""]

        messages = [{"role": "system", "content": system_prompt}]
        turns_respostas = []

        for i, turn_text in enumerate(turns):
            context_for_jinja = {**q, "turn_index": i, "current_turn": turn_text}

            turn_prompt = self.prompt_renderer.render(
                self.dataset_name, "user_template.minijinja", context_for_jinja
            )

            messages.append({"role": "user", "content": turn_prompt})

            try:
                resposta = self.ollama_client.generate_chat_response(model, messages)
            except Exception as e:
                resposta = f"ERRO: {e}"

            messages.append({"role": "assistant", "content": resposta})
            turns_respostas.append({"content": resposta})

        q_result["choices"] = [{"index": 0, "turns": turns_respostas}]
        q_result["ollama_response"] = "\n\n".join(t["content"] for t in turns_respostas)

        return q_result

    def _format_choices_for_final_answer(self, q_result: Dict[str, Any]) -> List[Any]:
        """Retorna as escolhas já formatadas pelo ``process_question``."""
        return q_result.get("choices", [])
