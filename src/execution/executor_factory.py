from src.execution.base import ExecutionManager
from src.execution.oab_bench_executor import OABBenchExecutionManager
from src.execution.oab_exams_executor import OABExamsExecutionManager

_EXECUTOR_REGISTRY = {
    "oab_bench": OABBenchExecutionManager,
    "oab_exams": OABExamsExecutionManager,
}


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
        """
        executor_class = _EXECUTOR_REGISTRY.get(dataset)
        if executor_class is None:
            raise ValueError(f"Dataset desconhecido: {dataset}")

        return executor_class(dataset_loader, storage, ollama_client)
