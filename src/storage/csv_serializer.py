"""Serialização e desserialização de arquivos no formato CSV."""

import csv
from pathlib import Path
from typing import Any, Dict, List

from src.storage.file_serializer import FileSerializer


class CsvSerializer(FileSerializer):
    """
    Implementação concreta de FileSerializer para o formato CSV.
    """

    def read(self, filepath: Path) -> List[Dict[str, Any]]:
        """Lê e desserializa um arquivo CSV para lista de dicionários."""
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [dict(row) for row in reader]

    def write(self, filepath: Path, data: List[Dict[str, Any]]) -> None:
        """Serializa e escreve uma lista de dicionários em formato CSV."""
        if not data:
            return

        keys = data[0].keys()
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
