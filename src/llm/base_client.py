import os
import uuid
from abc import ABC, abstractmethod
from typing import List


class BaseLLMClient(ABC):
    """
    Classe base abstrata para clientes de LLMs.
    """

    AVAILABLE_MODELS: List[str] = []

    def _validate_model(self, model: str) -> None:
        """Valida se o modelo informado está na lista de modelos suportados."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Modelo {model} não suportado. "
                f"Modelos disponíveis: {', '.join(self.AVAILABLE_MODELS)}"
            )

    def _save_debug_single_turn(
        self, model: str, system_prompt: str, user_prompt: str, response: str
    ) -> None:
        if os.environ.get("LLM_DEBUG") != "1":
            return

        safe_model_name = model.replace(":", "_").replace("/", "_")
        debug_dir = os.path.join(
            ".reinan_cache", "debug", safe_model_name, str(uuid.uuid4())
        )
        os.makedirs(debug_dir, exist_ok=True)

        with open(
            os.path.join(debug_dir, "system_prompt.md"), "w", encoding="utf-8"
        ) as f:
            f.write(system_prompt)

        with open(
            os.path.join(debug_dir, "user_prompt.md"), "w", encoding="utf-8"
        ) as f:
            f.write(user_prompt)

        with open(os.path.join(debug_dir, "response.md"), "w", encoding="utf-8") as f:
            f.write(response)

    def _save_debug_multi_turn(self, model: str, messages: list, response: str) -> None:
        if os.environ.get("LLM_DEBUG") != "1":
            return

        safe_model_name = model.replace(":", "_").replace("/", "_")
        debug_dir = os.path.join(
            ".reinan_cache", "debug", safe_model_name, str(uuid.uuid4())
        )
        os.makedirs(debug_dir, exist_ok=True)

        chat_history = ""
        for i, msg in enumerate(messages):
            role = str(msg.get("role", "unknown")).upper()
            content = str(msg.get("content", ""))
            chat_history += (
                f"### Message {i + 1} | Role: {role}\n\n{content}\n\n---\n\n"
            )

        with open(
            os.path.join(debug_dir, "chat_history.md"), "w", encoding="utf-8"
        ) as f:
            f.write(chat_history)

        with open(os.path.join(debug_dir, "response.md"), "w", encoding="utf-8") as f:
            f.write(response)

    def generate_response(
        self, model: str, system_prompt: str, user_prompt: str
    ) -> str:
        """
        Gera uma resposta síncrona usando um modelo específico (single-turn).
        """
        self._validate_model(model)
        response = self._generate_response(model, system_prompt, user_prompt)
        self._save_debug_single_turn(model, system_prompt, user_prompt, response)
        return response

    def generate_chat_response(self, model: str, messages: list) -> str:
        """
        Gera uma resposta síncrona a partir de uma lista de mensagens (multi-turn).
        """
        self._validate_model(model)
        response = self._generate_chat_response(model, messages)
        self._save_debug_multi_turn(model, messages, response)
        return response

    @abstractmethod
    def _generate_response(
        self, model: str, system_prompt: str, user_prompt: str
    ) -> str:
        """
        Implementação da geração de resposta síncrona usando um modelo específico (single-turn).
        """
        pass

    @abstractmethod
    def _generate_chat_response(self, model: str, messages: list) -> str:
        """
        Implementação da geração de resposta síncrona a partir de uma lista de mensagens (multi-turn).
        """
        pass
