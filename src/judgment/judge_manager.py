"""
Gerenciador de julgamento (LLM as a Judge).

Percorre as respostas dos modelos salvas em model_answer e gera
registros de julgamento para cada turn de cada questão.
"""

import time
from typing import Any, Dict, List

from src.storage.local_storage import LocalStorage

DEFAULT_JUDGE_MODEL = "gpt-5.2"


class JudgeManager:
    """
    Gerencia o processo de julgamento das respostas dos modelos
    utilizando a abordagem LLM as a Judge.
    """

    SUPPORTED_DATASETS = ["oab_bench"]

    def __init__(self, storage: LocalStorage, judge_model: str = DEFAULT_JUDGE_MODEL):
        self.storage = storage
        self.judge_model = judge_model

    def _load_model_answers(self, dataset: str, model: str) -> List[Dict[str, Any]]:
        """
        Carrega as respostas de um modelo específico a partir do cache.
        """
        filename = model.replace(":", "-")
        return self.storage.load_data(
            filename, fmt="json", sub_dir=f"results/{dataset}/model_answer"
        )

    def _build_judgment_record(
        self,
        question_id: str,
        model: str,
        answer_id: str,
        turn: int,
        prompt_type: str,
    ) -> Dict[str, Any]:
        """
        Constrói um registro de julgamento para um turn específico.
        """
        return {
            "question_id": question_id,
            "model": model,
            "answer_id": answer_id,
            "judge": self.judge_model,
            "prompt": prompt_type,
            "judgment": "",
            "score": 0.0,
            "turn": turn,
            "tstamp": time.time(),
        }

    def generate_judgments(
        self, dataset: str, model: str, limit: int = None
    ) -> List[Dict[str, Any]]:
        """
        Gera os registros de julgamento para todas as questões/turns
        de um modelo específico.

        Retorna a lista de registros de julgamento.
        """
        answers = self._load_model_answers(dataset, model)
        if limit is not None:
            answers = answers[:limit]

        judgments: List[Dict[str, Any]] = []

        for answer in answers:
            question_id = answer["question_id"]
            answer_id = answer["answer_id"]
            model_id = answer.get("model_id", model)

            model_name = model_id.replace(":", "-")

            choices = answer.get("choices", [])
            if not choices:
                continue

            turns = choices[0].get("turns", [])
            prompt_type = "single-turn" if len(turns) == 1 else "multi-turn"

            for turn_idx, _turn_content in enumerate(turns):
                record = self._build_judgment_record(
                    question_id=question_id,
                    model=model_name,
                    answer_id=answer_id,
                    turn=turn_idx + 1,
                    prompt_type=prompt_type,
                )
                judgments.append(record)

        return judgments

    def save_judgments(self, dataset: str, judgments: List[Dict[str, Any]]) -> str:
        """
        Salva os registros de julgamento em um arquivo JSON no diretório
        model_judgment, usando o nome do modelo juiz como nome do arquivo.
        """
        filename = self.judge_model.replace(":", "-")
        output_path = self.storage.save_data(
            judgments,
            filename,
            fmt="json",
            sub_dir=f"results/{dataset}/model_judgment",
        )
        return str(output_path)

    def run(self, dataset: str, models: List[str], limit: int = None) -> str:
        """
        Executa o fluxo completo de geração de julgamentos para todos
        os modelos informados e salva o resultado.

        Retorna o caminho do arquivo de saída.
        """
        all_judgments: List[Dict[str, Any]] = []

        for model in models:
            model_judgments = self.generate_judgments(dataset, model, limit=limit)
            all_judgments.extend(model_judgments)

        output_path = self.save_judgments(dataset, all_judgments)
        return output_path
