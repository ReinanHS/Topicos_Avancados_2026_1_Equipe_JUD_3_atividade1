"""Serialização e desserialização de arquivos no formato JSON."""

import json
from pathlib import Path
from typing import Any, Dict, List

from src.storage.file_serializer import FileSerializer


class JsonSerializer(FileSerializer):
    """
    Implementação concreta de FileSerializer para o formato JSON.
    """

    def read(self, filepath: Path) -> List[Dict[str, Any]]:
        """Lê e desserializa um arquivo JSON para lista de dicionários."""
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def write(self, filepath: Path, data: List[Dict[str, Any]]) -> None:
        """Serializa e escreve uma lista de dicionários em formato JSON."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
