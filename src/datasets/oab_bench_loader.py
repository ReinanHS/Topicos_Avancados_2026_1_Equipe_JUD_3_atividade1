import json
from typing import Any, Dict, List

import requests

from src.datasets.base import DatasetLoader


class OABBenchLoader(DatasetLoader):
    """
    Carregador para o dataset maritaca-ai/oab-bench.

    Faz download direto dos arquivos JSONL hospedados no GitHub
    e retorna o lote designado (questões 176 a 188).
    """

    COMMIT = "e9a83acd65ba590bd032922c4ba0bfeaa5f58e8b"
    REPO_NAME = "maritaca-ai/oab-bench"

    QUESTIONS_PATH = "data/oab_bench/question.jsonl"
    REFERENCES_PATH = "data/oab_bench/reference_answer/guidelines.jsonl"

    SLICE_START = 176
    SLICE_END = 188

    def _load_jsonl_from_github(self, file_path: str) -> List[Dict[str, Any]]:
        """Faz download e parseia um arquivo JSONL do repositório GitHub."""
        url = (
            f"https://raw.githubusercontent.com/"
            f"{self.REPO_NAME}/{self.COMMIT}/{file_path}"
        )
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(
                f"Erro ao baixar o arquivo do repositório "
                f"{self.REPO_NAME}: {response.status_code}"
            )

        questions = []
        for line in response.iter_lines():
            if line:
                questions.append(json.loads(line))

        return questions

    def load_questions(self) -> List[Dict[str, Any]]:
        """Baixa as questões do oab-bench e retorna o lote designado."""
        questions = self._load_jsonl_from_github(self.QUESTIONS_PATH)
        return questions[self.SLICE_START : self.SLICE_END]

    def load_references(self) -> List[Dict[str, Any]]:
        """Baixa as guidelines de referência do oab-bench e retorna o lote designado."""
        references = self._load_jsonl_from_github(self.REFERENCES_PATH)
        return references[self.SLICE_START : self.SLICE_END]
