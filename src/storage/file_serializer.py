"""Contrato abstrato para serialização e desserialização de arquivos."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List


class FileSerializer(ABC):
    """
    Classe base abstrata que define o contrato para leitura e escrita
    de arquivos em um formato específico (ex: JSON, CSV).
    """

    @abstractmethod
    def read(self, filepath: Path) -> List[Dict[str, Any]]:
        """
        Lê o conteúdo de um arquivo e retorna uma lista de dicionários.

        Args:
            filepath: Caminho absoluto do arquivo a ser lido.

        Returns:
            Lista de dicionários com os dados do arquivo.

        Raises:
            FileNotFoundError: Se o arquivo não existir.
        """

    @abstractmethod
    def write(self, filepath: Path, data: List[Dict[str, Any]]) -> None:
        """
        Escreve uma lista de dicionários em um arquivo.

        Args:
            filepath: Caminho absoluto do arquivo de destino.
            data: Lista de dicionários a ser salva.
        """
