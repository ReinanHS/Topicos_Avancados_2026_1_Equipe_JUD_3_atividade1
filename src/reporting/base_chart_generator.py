from abc import ABC, abstractmethod
import seaborn as sns
import matplotlib

from src.storage.local_storage import LocalStorage

matplotlib.use("Agg")


class BaseChartGenerator(ABC):
    """
    Classe base para geração de gráficos.
    """

    def __init__(self, dataset: str):
        self.dataset = dataset
        self.storage = LocalStorage()
        self.outputs_dir = self.storage.cache_dir / "results" / self.dataset / "charts"
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        sns.set_theme(style="whitegrid", font_scale=1.1)

    @abstractmethod
    def generate_all_charts(self):
        """
        Executa a leitura dos dados e a geração de todos os gráficos específicos
        para o dataset fornecido.
        """
        pass
