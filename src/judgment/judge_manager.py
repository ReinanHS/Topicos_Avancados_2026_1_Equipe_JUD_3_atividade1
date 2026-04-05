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
        import jinja2
        import re
        from src.datasets.loader_factory import DatasetLoaderFactory
        from src.llm.openai_client import OpenAIClient

        answers = self._load_model_answers(dataset, model)
        if limit is not None:
            answers = answers[:limit]

        loader = DatasetLoaderFactory.create(dataset)
        questions_data = loader.load_questions()
        q_map = {q["question_id"]: q for q in questions_data}

        references = (
            loader.load_references() if hasattr(loader, "load_references") else []
        )
        ref_map = {}
        for r in references:
            choices = r.get("choices", [])
            if choices:
                ref_map[r["question_id"]] = [
                    t if isinstance(t, str) else str(t)
                    for t in choices[0].get("turns", [])
                ]

        jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader("prompts/judge"))
        tmpl_single_sys = jinja_env.get_template(
            "single-turn/system_template.minijinja"
        )
        tmpl_single_usr = jinja_env.get_template("single-turn/user_template.minijinja")
        tmpl_multi_sys = jinja_env.get_template("multi-turn/system_template.minijinja")
        tmpl_multi_usr = jinja_env.get_template("multi-turn/user_template.minijinja")

        llm = OpenAIClient()
        if self.judge_model not in llm.AVAILABLE_MODELS:
            llm.AVAILABLE_MODELS.append(self.judge_model)

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

            q_info = q_map.get(question_id, {})
            r_info = ref_map.get(question_id, [])

            stmt = q_info.get("statement", "")
            q_turns = q_info.get("turns", [])
            q_values = q_info.get("values", [])

            for turn_idx, turn_content in enumerate(turns):
                record = self._build_judgment_record(
                    question_id=question_id,
                    model=model_name,
                    answer_id=answer_id,
                    turn=turn_idx + 1,
                    prompt_type=prompt_type,
                )

                val = q_values[turn_idx] if turn_idx < len(q_values) else 0.0

                if prompt_type == "single-turn":
                    sys_prompt = tmpl_single_sys.render(value=val)
                    q_text = stmt + "\n" + q_turns[0] if q_turns else stmt
                    ref_text = r_info[0] if r_info else ""
                    ans_content = (
                        turn_content.get("content", "")
                        if isinstance(turn_content, dict)
                        else str(turn_content)
                    )

                    usr_prompt = tmpl_single_usr.render(
                        question=q_text, ref_answer_1=ref_text, answer=ans_content
                    )
                else:
                    sys_prompt = tmpl_multi_sys.render(value=val)
                    q1 = stmt + "\n" + q_turns[0] if len(q_turns) > 0 else stmt
                    q2 = q_turns[1] if len(q_turns) > 1 else ""
                    ref1 = r_info[0] if len(r_info) > 0 else ""
                    ref2 = r_info[1] if len(r_info) > 1 else ""

                    ans1 = (
                        turns[0].get("content", "")
                        if len(turns) > 0 and isinstance(turns[0], dict)
                        else str(turns[0])
                        if len(turns) > 0
                        else ""
                    )
                    ans2 = (
                        turns[1].get("content", "")
                        if len(turns) > 1 and isinstance(turns[1], dict)
                        else str(turns[1])
                        if len(turns) > 1
                        else ""
                    )

                    usr_prompt = tmpl_multi_usr.render(
                        question_1=q1,
                        question_2=q2,
                        ref_answer_1=ref1,
                        ref_answer_2=ref2,
                        answer_1=ans1,
                        answer_2=ans2,
                    )

                try:
                    res_text = llm.generate_response(
                        self.judge_model, sys_prompt, usr_prompt
                    )
                    record["judgment"] = res_text

                    match = re.search(r"\[\[([\d.,]+)\]\]", res_text)
                    if match:
                        score_str = match.group(1).replace(",", ".")
                        record["score"] = float(score_str)
                except Exception as e:
                    print(f"Erro ao avaliar {question_id} turn {turn_idx + 1}: {e}")

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
