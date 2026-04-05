from typing import Any, Dict, List

from src.datasets.base import DatasetLoader


class OABExamsLoader(DatasetLoader):
    """
    Carregador para o dataset eduagarcia/oab_exams.

    Utiliza a biblioteca HuggingFace `datasets` para baixar e retornar
    o lote designado (registros 1845 a 1967).
    """

    DATASET_NAME = "eduagarcia/oab_exams"

    SLICE_START = 1845
    SLICE_END = 1967

    def load_questions(self) -> List[Dict[str, Any]]:
        """Baixa as questões do oab_exams via HuggingFace e retorna o lote designado."""
        from datasets import load_dataset

        ds_exams = load_dataset(self.DATASET_NAME)
        questions = list(ds_exams["train"])
        return questions[self.SLICE_START : self.SLICE_END]

    def load_references(self) -> List[Dict[str, Any]]:
        """
        O dataset oab_exams não possui respostas de referência separadas.
        O gabarito está embutido no campo `answerKey` de cada questão.
        """
        return []
