from openai import OpenAI
from src.llm.base_client import BaseLLMClient


class OpenAIClient(BaseLLMClient):
    """
    Wrapper do SDK OpenAI para integração e execução de LLMs na nuvem.
    """

    AVAILABLE_MODELS = [
        "gpt-3.5-turbo",
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4o",
        "gpt-4o-mini",
    ]

    def __init__(self, api_key: str = None):
        """
        Inicializa o cliente OpenAI.
        A API key será lida por padrão da variável de ambiente OPENAI_API_KEY.
        """
        self.client = OpenAI(api_key=api_key)

    def generate_response(
        self, model: str, system_prompt: str, user_prompt: str
    ) -> str:
        """
        Gera uma resposta síncrona da OpenAI usando um modelo específico (single-turn).
        """
        self._validate_model(model)

        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content

    def generate_chat_response(self, model: str, messages: list) -> str:
        """
        Gera uma resposta síncrona da OpenAI a partir de uma lista
        de mensagens (multi-turn).
        """
        self._validate_model(model)

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
        )
        return response.choices[0].message.content
