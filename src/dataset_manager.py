from typing import List, Dict, Any


class DatasetManager:
    """
    Classe responsável por gerenciar a carga e o pré-processamento
    dos datasets da OAB utilizados na aplicação.
    """

    OAB_BENCH_COMMIT = "e9a83acd65ba590bd032922c4ba0bfeaa5f58e8b"
    OAB_BENCH_REPO_NAME = "maritaca-ai/oab-bench"

    def __init__(self):
        pass

    def load_file_from_github(self, repo_name: str, branch: str, file_path: str) -> List[Dict[str, Any]]:
        import requests
        import json

        repo_url = f"https://raw.githubusercontent.com/{repo_name}/{branch}/{file_path}"
        response = requests.get(repo_url)
        if response.status_code != 200:
            raise Exception(f"Erro ao baixar o arquivo do repositório {repo_name}: {response.status_code}")

        questions = []
        for line in response.iter_lines():
            if line:
                questions.append(json.loads(line))
        
        return questions

    def load_oab_bench_reference_answers(self) -> List[Dict[str, Any]]:
        """
        Baixa as coleções de guidelines do maritaca-ai/oab-bench.
        """
        questions = self.load_file_from_github(self.OAB_BENCH_REPO_NAME, self.OAB_BENCH_COMMIT, "data/oab_bench/reference_answer/guidelines.jsonl")
        return questions[176:188]

    def load_oab_bench_questions(self) -> List[Dict[str, Any]]:
        """
        Baixa as questões do maritaca-ai/oab-bench e retorna o lote designado.
        """
        questions = self.load_file_from_github(self.OAB_BENCH_REPO_NAME, self.OAB_BENCH_COMMIT, "data/oab_bench/question.jsonl")
        return questions[176:188]

    def load_oab_exams_questions(self) -> List[Dict[str, Any]]:
        """
        Baixa as questões do eduagarcia/oab_exams e retorna o lote designado.
        """
        from datasets import load_dataset

        ds_exams = load_dataset("eduagarcia/oab_exams")

        questions = list(ds_exams["train"])
        return questions[1845:1967]
