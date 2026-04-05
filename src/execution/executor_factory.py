from src.execution.base import ExecutionManager
from src.execution.oab_bench_executor import OABBenchExecutionManager
from src.execution.oab_exams_executor import OABExamsExecutionManager


class ExecutionManagerFactory:
    """
    Fábrica responsável por criar a instância especializada correta
    de ExecutionManager com base no nome do dataset.
    """

    @staticmethod
    def create(
        dataset: str, dataset_loader, storage, ollama_client
    ) -> ExecutionManager:
        """
        Cria o executor adequado para o dataset informado.

        Args:
            dataset: Nome do dataset (ex.: "oab_bench", "oab_exams").
            dataset_loader: Instância do carregador de dados.
            storage: Instância do gerenciador de armazenamento.
            ollama_client: Instância do client Ollama.

        Raises:
            ValueError: Se o dataset não for reconhecido.
        """
        if dataset == "oab_bench":
            return OABBenchExecutionManager(dataset_loader, storage, ollama_client)
        elif dataset == "oab_exams":
            return OABExamsExecutionManager(dataset_loader, storage, ollama_client)
        else:
            raise ValueError(f"Dataset desconhecido: {dataset}")
