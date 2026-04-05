import time
import httpx
import ollama
from src.llm.base_client import BaseLLMClient


class OllamaClient(BaseLLMClient):
    """
    Wrapper do SDK Ollama para integração e execução de LLMs locais.
    """

    AVAILABLE_MODELS = ["llama3.2:3b", "gemma2:2b", "qwen2.5:3b"]

    def __init__(self, timeout_seconds: float = 300.0, max_retries: int = 3):
        self.max_retries = max_retries
        self.client = ollama.Client(
            host="http://127.0.0.1:11434", timeout=httpx.Timeout(timeout_seconds)
        )

    def _execute_with_retry(self, operation_func):
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return operation_func()
            except Exception as e:
                last_exception = e
                if attempt == self.max_retries:
                    break
                print(
                    f"[OllamaClient] Falha na tentativa {attempt}/{self.max_retries} ({type(e).__name__}: {e}). Retentando em 5 segundos..."
                )
                time.sleep(5)

        raise RuntimeError(
            f"Falha crítica no Ollama após {self.max_retries} tentativas. "
            f"Erro original: {last_exception}.\n"
            "Isso geralmente ocorre quando o motor interno do Ollama (llama.cpp) trava no estado "
            "'Stopping...' ou sofre estrangulamento de memória VRAM ao trocar rapidamente entre modelos.\n"
            "RECOMENDAÇÃO: Interrompa o serviço do Ollama (Gerenciador de Tarefas ou Tray) "
            "e reinicie manualmente para limpar a memória da placa de vídeo."
        ) from last_exception

    def _generate_response(
        self, model: str, system_prompt: str, user_prompt: str
    ) -> str:
        """
        Gera uma resposta síncrona do Ollama usando um modelo específico (single-turn).
        """

        def _call_api():
            response = self.client.chat(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response["message"]["content"]

        return self._execute_with_retry(_call_api)

    def _generate_chat_response(self, model: str, messages: list) -> str:
        """
        Gera uma resposta síncrona do Ollama a partir de uma lista
        de mensagens (multi-turn).
        """

        def _call_api():
            response = self.client.chat(
                model=model,
                messages=messages,
            )
            return response["message"]["content"]

        return self._execute_with_retry(_call_api)
