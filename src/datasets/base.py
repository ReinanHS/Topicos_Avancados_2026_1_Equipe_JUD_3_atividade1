from abc import ABC, abstractmethod
from typing import Any, Dict, List


class DatasetLoader(ABC):
    """
    Contrato base para carregadores de datasets da OAB.

    Cada implementação concreta é responsável por buscar os dados
    de sua respectiva fonte (GitHub, HuggingFace Hub, etc.)
    e retornar o lote designado de questões.
    """

    @abstractmethod
    def load_questions(self) -> List[Dict[str, Any]]:
        """Carrega e retorna a lista de questões do dataset."""
        ...

    @abstractmethod
    def load_references(self) -> List[Dict[str, Any]]:
        """
        Carrega e retorna respostas de referência / gabaritos.

        Deve retornar lista vazia caso o dataset não possua referências.
        """
        ...
