import itertools
import re
from typing import Any, Dict, List


class CrossModelEvaluator:
    """
    Avaliador pairwise: compara respostas entre pares de modelos
    utilizando métricas BLEU, ROUGE e BERTScore.
    Também compara cada modelo contra as guidelines de referência.
    """

    def __init__(self, storage):
        self.storage = storage
        self._metrics_cache = {}

    def _get_metric(self, name: str):
        """Carrega uma métrica do `evaluate` sob demanda e guarda em cache."""
        if name not in self._metrics_cache:
            import evaluate

            self._metrics_cache[name] = evaluate.load(name)
        return self._metrics_cache[name]

    @staticmethod
    def _extract_turns(answer: dict) -> List[str]:
        """
        Extrai a lista de conteúdos dos turns de uma resposta de modelo.
        """
        choices = answer.get("choices", [])
        if not choices:
            return []
        turns = choices[0].get("turns", [])
        return [t.get("content", "") for t in turns]

    @staticmethod
    def _format_guideline_turn(turn_text: str) -> str:
        """
        Formata o texto da guideline: remove a seção de distribuição de pontos
        e limpa quebras de linha e espaços em branco duplicados.
        """
        idx = turn_text.find("DISTRIBUIÇÃO DE PONTOS")
        if idx != -1:
            turn_text = turn_text[:idx]

        turn_text = turn_text.replace("\n", " ").replace("\r", " ")
        return re.sub(r"\s+", " ", turn_text).strip()

    @staticmethod
    def _extract_reference_turns(reference: dict) -> List[str]:
        """
        Extrai e formata a lista de turns de uma referência (guideline).
        """
        choices = reference.get("choices", [])
        if not choices:
            return []
        turns = choices[0].get("turns", [])
        extracted = [t if isinstance(t, str) else str(t) for t in turns]
        return [CrossModelEvaluator._format_guideline_turn(t) for t in extracted]

    def _compute_pair_metrics(
        self, predictions: List[str], references: List[str]
    ) -> Dict[str, float]:
        """Calcula BLEU, ROUGE e BERTScore para um par de listas de textos."""
        if not predictions:
            return {}

        bleu_score = self._get_metric("bleu").compute(
            predictions=predictions, references=references
        )
        rouge_score = self._get_metric("rouge").compute(
            predictions=predictions, references=references
        )
        bert_score_raw = self._get_metric("bertscore").compute(
            predictions=predictions, references=references, lang="pt"
        )
        bert_f1_mean = (
            sum(bert_score_raw["f1"]) / len(bert_score_raw["f1"])
            if bert_score_raw["f1"]
            else 0.0
        )

        return {
            "bleu": bleu_score.get("bleu", 0.0),
            "rouge1": rouge_score.get("rouge1", 0.0),
            "rouge2": rouge_score.get("rouge2", 0.0),
            "rougeL": rouge_score.get("rougeL", 0.0),
            "bertscore_f1": bert_f1_mean,
        }

    def _load_model_answers(
        self, dataset_name: str, models: list
    ) -> Dict[str, Dict[str, List[str]]]:
        """
        Carrega as respostas de cada modelo e organiza por question_id.
        """
        all_results = {}
        for model in models:
            filename = model.replace(":", "-")
            results = self.storage.load_data(
                filename, fmt="json", sub_dir=f"results/{dataset_name}/model_answer"
            )
            model_responses = {}
            for res in results:
                qid = res["question_id"]
                turns = self._extract_turns(res)
                model_responses[qid] = turns
            all_results[model] = model_responses
        return all_results

    def _load_guideline_references(self, dataset_name: str) -> Dict[str, List[str]]:
        """
        Carrega as guidelines de referência usando o loader do dataset.
        Retorna um dicionário question_id -> lista de turns (strings).
        """
        from src.datasets.loader_factory import DatasetLoaderFactory

        loader = DatasetLoaderFactory.create(dataset_name)

        if not hasattr(loader, "load_references"):
            return {}

        references = loader.load_references()
        guideline_map = {}
        for ref in references:
            qid = ref.get("question_id", "")
            if qid:
                guideline_map[qid] = self._extract_reference_turns(ref)
        return guideline_map

    @staticmethod
    def _detect_num_turns(all_results: Dict[str, Dict[str, List[str]]]) -> int:
        """Detecta o número de turns a partir dos dados carregados."""
        for model_responses in all_results.values():
            for turns in model_responses.values():
                return len(turns)
        return 0

    def _compute_turn_scores(
        self,
        source_responses: Dict[str, List[str]],
        target_responses: Dict[str, List[str]],
        num_turns: int,
    ) -> Dict[str, Dict[str, float]]:
        """
        Calcula as métricas por turn entre duas fontes de respostas,
        incluindo a média agregada.
        """
        common_qs = set(source_responses.keys()) & set(target_responses.keys())
        if not common_qs:
            return {}

        turn_scores = {}

        for turn_idx in range(num_turns):
            predictions = []
            references = []

            for q_id in common_qs:
                src_turns = source_responses[q_id]
                tgt_turns = target_responses[q_id]

                if turn_idx < len(src_turns) and turn_idx < len(tgt_turns):
                    src_text = src_turns[turn_idx]
                    tgt_text = tgt_turns[turn_idx]
                    if src_text and tgt_text:
                        predictions.append(src_text)
                        references.append(tgt_text)

            metrics = self._compute_pair_metrics(predictions, references)
            if metrics:
                turn_scores[f"turn_{turn_idx + 1}"] = metrics

        if not turn_scores:
            return {}

        metric_keys = list(next(iter(turn_scores.values())).keys())
        avg_metrics = {}
        for mk in metric_keys:
            values = [turn_scores[t][mk] for t in turn_scores if mk in turn_scores[t]]
            avg_metrics[mk] = sum(values) / len(values) if values else 0.0

        return {**turn_scores, "average": avg_metrics}

    def evaluate(self, dataset_name: str, models: list) -> Dict[str, Dict[str, Any]]:
        """
        Executa a avaliação cruzada (pairwise) entre os modelos disponíveis
        e também compara cada modelo contra as guidelines de referência.
        """
        if len(models) < 2:
            raise ValueError(
                "São necessários pelo menos 2 modelos para rodar a avaliação cruzada."
            )

        all_results = self._load_model_answers(dataset_name, models)
        num_turns = self._detect_num_turns(all_results)

        if num_turns == 0:
            return {}

        cross_scores = {}

        pairs = list(itertools.combinations(models, 2))
        for model_ref, model_pred in pairs:
            scores = self._compute_turn_scores(
                all_results[model_pred], all_results[model_ref], num_turns
            )
            if scores:
                cross_scores[f"{model_ref} vs {model_pred}"] = scores

        guideline_map = self._load_guideline_references(dataset_name)
        if guideline_map:
            for model in models:
                scores = self._compute_turn_scores(
                    all_results[model], guideline_map, num_turns
                )
                if scores:
                    cross_scores[f"{model} vs guideline"] = scores

        return cross_scores
