"""Gerenciamento de armazenamento local com suporte a múltiplos formatos."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from src.storage.csv_serializer import CsvSerializer
from src.storage.file_serializer import FileSerializer
from src.storage.json_serializer import JsonSerializer


class LocalStorage:
    """
    Gerencia o armazenamento local de arquivos em um diretório de cache reservado.
    """

    def __init__(self, cache_dir: str = ".reinan_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._serializers: Dict[str, FileSerializer] = {
            "json": JsonSerializer(),
            "csv": CsvSerializer(),
        }

    def save_data(
        self,
        data: List[Dict[str, Any]],
        filename: str,
        fmt: str = "json",
        sub_dir: Optional[str] = None,
    ) -> Path:
        """
        Salva a lista de dicionários num arquivo dentro da pasta de cache.

        Args:
            data: Lista de dicionários a ser salva.
            filename: Nome do arquivo (sem extensão).
            fmt: Formato do arquivo ('json' ou 'csv').
            sub_dir: Subdiretório opcional dentro do cache.

        Returns:
            Caminho completo do arquivo salvo.

        Raises:
            ValueError: Se o formato não for suportado.
        """
        serializer = self._get_serializer(fmt)
        target_dir = self._resolve_target_dir(sub_dir, create=True)
        filepath = target_dir / f"{filename}.{fmt}"

        serializer.write(filepath, data)
        return filepath

    def load_data(
        self,
        filename: str,
        fmt: str = "json",
        sub_dir: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Carrega dados de um arquivo no diretório de cache.

        Args:
            filename: Nome do arquivo (sem extensão).
            fmt: Formato do arquivo ('json' ou 'csv').
            sub_dir: Subdiretório opcional dentro do cache.

        Returns:
            Lista de dicionários com os dados carregados.

        Raises:
            FileNotFoundError: Se o arquivo não existir.
            ValueError: Se o formato não for suportado.
        """
        serializer = self._get_serializer(fmt)
        target_dir = self._resolve_target_dir(sub_dir)
        filepath = target_dir / f"{filename}.{fmt}"

        if not filepath.exists():
            raise FileNotFoundError(f"Arquivo não encontrado no diretório: {filepath}")

        return serializer.read(filepath)

    def list_available_models(
        self, dataset_name: str, sub_dir: str = "results"
    ) -> List[str]:
        """
        Retorna os nomes dos modelos com resultados salvos para um dataset.

        Args:
            dataset_name: Nome do dataset a ser consultado.
            sub_dir: Subdiretório base dos resultados.

        Returns:
            Lista de nomes de modelos disponíveis.
        """
        target_dir = self.cache_dir / "results" / dataset_name / "model_answer"

        if not target_dir.exists():
            return []

        return [self._parse_model_name(file.name) for file in target_dir.glob("*.json")]

    def _resolve_target_dir(self, sub_dir: Optional[str], create: bool = False) -> Path:
        """
        Resolve o diretório de destino a partir do subdiretório opcional.

        Args:
            sub_dir: Subdiretório opcional dentro do cache.
            create: Se True, cria o diretório caso não exista.

        Returns:
            Caminho do diretório resolvido.
        """
        if not sub_dir:
            return self.cache_dir

        target_dir = self.cache_dir / sub_dir

        if create:
            target_dir.mkdir(parents=True, exist_ok=True)

        return target_dir

    def _get_serializer(self, fmt: str) -> FileSerializer:
        """
        Retorna o serializer correspondente ao formato solicitado.

        Args:
            fmt: Formato do arquivo ('json', 'csv', etc.).

        Returns:
            Instância de FileSerializer para o formato.

        Raises:
            ValueError: Se o formato não for suportado.
        """
        serializer = self._serializers.get(fmt)

        if not serializer:
            formatos = ", ".join(self._serializers.keys())
            raise ValueError(
                f"Formato '{fmt}' não suportado. Formatos disponíveis: {formatos}"
            )

        return serializer

    @staticmethod
    def _parse_model_name(filename: str) -> str:
        """
        Converte o nome de arquivo em nome de modelo.

        Exemplo: 'gemma-3-4b' -> 'gemma:3:4b'

        Args:
            filename: Nome do arquivo com extensão .json.

        Returns:
            Nome do modelo com separadores ':'.
        """
        name_without_extension = filename.removesuffix(".json")
        return name_without_extension.replace("-", ":")
