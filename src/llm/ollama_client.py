import ollama


class OllamaClient:
    """
    Wrapper do SDK Ollama para integração e execução de LLMs locais.
    """

    AVAILABLE_MODELS = ["llama3.2:3b", "gemma2:2b", "qwen2.5:3b"]

    def __init__(self):
        self.client = ollama.Client()

    def _validate_model(self, model: str) -> None:
        """Valida se o modelo informado está na lista de modelos suportados."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Modelo {model} não suportado. "
                f"Modelos disponíveis: {', '.join(self.AVAILABLE_MODELS)}"
            )

    def generate_response(
        self, model: str, system_prompt: str, user_prompt: str
    ) -> str:
        """
        Gera uma resposta síncrona do Ollama usando um modelo específico (single-turn).
        """
        self._validate_model(model)

        response = self.client.chat(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response["message"]["content"]

    def generate_chat_response(self, model: str, messages: list) -> str:
        """
        Gera uma resposta síncrona do Ollama a partir de uma lista
        de mensagens (multi-turn).
        """
        self._validate_model(model)

        response = self.client.chat(
            model=model,
            messages=messages,
        )
        return response["message"]["content"]
