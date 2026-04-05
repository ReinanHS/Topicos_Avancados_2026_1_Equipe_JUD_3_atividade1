from src.datasets.base import DatasetLoader
from src.datasets.oab_bench_loader import OABBenchLoader
from src.datasets.oab_exams_loader import OABExamsLoader


class DatasetLoaderFactory:
    """
    Fábrica responsável por instanciar o carregador de dataset correto
    a partir do nome do dataset.
    """

    _registry = {
        "oab_bench": OABBenchLoader,
        "oab_exams": OABExamsLoader,
    }

    @classmethod
    def create(cls, dataset_name: str) -> DatasetLoader:
        """
        Cria e retorna a instância do loader correspondente ao dataset.

        Raises:
            ValueError: Se o dataset não estiver no registro.
        """
        loader_class = cls._registry.get(dataset_name)
        if loader_class is None:
            available = ", ".join(cls._registry.keys())
            raise ValueError(
                f"Dataset '{dataset_name}' não reconhecido. Disponíveis: {available}"
            )
        return loader_class()

    @classmethod
    def available_datasets(cls) -> list[str]:
        """Retorna a lista de datasets registrados."""
        return list(cls._registry.keys())
