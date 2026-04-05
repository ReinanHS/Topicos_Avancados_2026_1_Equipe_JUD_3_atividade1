import itertools
from typing import Any, Dict, List


class CrossModelEvaluator:
    """
    Avaliador pairwise: compara respostas entre pares de modelos
    utilizando métricas BLEU, ROUGE e BERTScore.
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
        Extrai a lista de conteúdos dos turns de uma resposta.
        """
        choices = answer.get("choices", [])
        if not choices:
            return []
        turns = choices[0].get("turns", [])
        return [t.get("content", "") for t in turns]

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

    @staticmethod
    def _detect_num_turns(all_results: Dict[str, Dict[str, List[str]]]) -> int:
        """Detecta o número de turns a partir dos dados carregados."""
        for model_responses in all_results.values():
            for turns in model_responses.values():
                return len(turns)
        return 0

    def evaluate(self, dataset_name: str, models: list) -> Dict[str, Dict[str, Any]]:
        """
        Executa a avaliação cruzada (pairwise) entre os modelos disponíveis.
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
            common_qs = set(all_results[model_ref].keys()) & set(
                all_results[model_pred].keys()
            )

            if not common_qs:
                continue

            turn_scores = {}

            for turn_idx in range(num_turns):
                predictions = []
                references = []

                for q_id in common_qs:
                    ref_turns = all_results[model_ref][q_id]
                    pred_turns = all_results[model_pred][q_id]

                    if turn_idx < len(ref_turns) and turn_idx < len(pred_turns):
                        ref_text = ref_turns[turn_idx]
                        pred_text = pred_turns[turn_idx]
                        if ref_text and pred_text:
                            references.append(ref_text)
                            predictions.append(pred_text)

                metrics = self._compute_pair_metrics(predictions, references)
                if metrics:
                    turn_scores[f"turn_{turn_idx + 1}"] = metrics

            if not turn_scores:
                continue

            metric_keys = list(next(iter(turn_scores.values())).keys())
            avg_metrics = {}
            for mk in metric_keys:
                values = [
                    turn_scores[t][mk] for t in turn_scores if mk in turn_scores[t]
                ]
                avg_metrics[mk] = sum(values) / len(values) if values else 0.0

            pair_name = f"{model_ref} vs {model_pred}"
            cross_scores[pair_name] = {
                **turn_scores,
                "average": avg_metrics,
            }

        return cross_scores
