from typing import Dict


class ExactMatchEvaluator:
    """
    Avaliador exato: calcula Acurácia, Precisão, Recall e F1
    para modelos que produzem respostas objetivas (múltipla escolha).
    """

    LETTER_TO_INT = {"A": 1, "B": 2, "C": 3, "D": 4}

    def __init__(self, storage):
        self.storage = storage
        self._metrics_cache = {}

    def _get_metric(self, name: str):
        """Carrega uma métrica do `evaluate` sob demanda e guarda em cache."""
        if name not in self._metrics_cache:
            import evaluate

            self._metrics_cache[name] = evaluate.load(name)
        return self._metrics_cache[name]

    def evaluate(self, dataset_name: str, models: list) -> Dict[str, Dict[str, float]]:
        """
        Executa a avaliação exata para os modelos disponíveis
        usando Acurácia, Precisão, Recall e F1.
        """
        all_results = {}

        for model in models:
            filename = f"{dataset_name}_{model.replace(':', '-')}_results"
            results = self.storage.load_data(filename, fmt="json", sub_dir="results")

            predictions = []
            references = []

            for res in results:
                ref = res.get("answerKey", "")
                pred = res.get("objective_answer", "")

                ref_int = self.LETTER_TO_INT.get(ref, -1)
                pred_int = self.LETTER_TO_INT.get(pred, 0)

                references.append(ref_int)
                predictions.append(pred_int)

            if not predictions:
                continue

            acc_score = self._get_metric("accuracy").compute(
                predictions=predictions, references=references
            )
            prec_score = self._get_metric("precision").compute(
                predictions=predictions,
                references=references,
                average="macro",
                zero_division=0,
            )
            rec_score = self._get_metric("recall").compute(
                predictions=predictions,
                references=references,
                average="macro",
                zero_division=0,
            )
            f1_score = self._get_metric("f1").compute(
                predictions=predictions, references=references, average="macro"
            )

            all_results[model] = {
                "accuracy": acc_score.get("accuracy", 0.0),
                "precision": prec_score.get("precision", 0.0),
                "recall": rec_score.get("recall", 0.0),
                "f1": f1_score.get("f1", 0.0),
            }

        return all_results
