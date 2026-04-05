import ollama
from src.llm.base_client import BaseLLMClient


class OllamaClient(BaseLLMClient):
    """
    Wrapper do SDK Ollama para integração e execução de LLMs locais.
    """

    AVAILABLE_MODELS = ["llama3.2:3b", "gemma2:2b", "qwen2.5:3b"]

    def __init__(self):
        self.client = ollama.Client()

    def _generate_response(
        self, model: str, system_prompt: str, user_prompt: str
    ) -> str:
        """
        Gera uma resposta síncrona do Ollama usando um modelo específico (single-turn).
        """
        response = self.client.chat(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response["message"]["content"]

    def _generate_chat_response(self, model: str, messages: list) -> str:
        """
        Gera uma resposta síncrona do Ollama a partir de uma lista
        de mensagens (multi-turn).
        """
        response = self.client.chat(
            model=model,
            messages=messages,
        )
        return response["message"]["content"]
