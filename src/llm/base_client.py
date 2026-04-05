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

    @abstractmethod
    def generate_response(
        self, model: str, system_prompt: str, user_prompt: str
    ) -> str:
        """
        Gera uma resposta síncrona usando um modelo específico (single-turn).
        """
        pass

    @abstractmethod
    def generate_chat_response(self, model: str, messages: list) -> str:
        """
        Gera uma resposta síncrona a partir de uma lista de mensagens (multi-turn).
        """
        pass
