from abc import ABC, abstractmethod
import matplotlib.pyplot as plt
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

    def _add_bar_labels(self, ax, bars, fmt=".3f", fontsize=8, padding=0.008):
        """
        Adiciona rótulos de valor acima de cada barra de um gráfico.
        """
        for bar in bars:
            height = bar.get_height()
            if height == 0 and fmt == "d":
                continue
            label = f"{int(height)}" if fmt == "d" else f"{height:{fmt}}"
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + padding,
                label,
                ha="center",
                va="bottom",
                fontsize=fontsize,
            )

    def _add_barh_labels(self, ax, bars, fontsize=8, padding=0.1):
        """
        Adiciona rótulos de valor ao lado direito de barras horizontais.
        """
        for bar in bars:
            width = bar.get_width()
            if width > 0:
                ax.text(
                    width + padding,
                    bar.get_y() + bar.get_height() / 2,
                    f"{int(width)}",
                    ha="left",
                    va="center",
                    fontsize=fontsize,
                )

    def _save_and_close(self, filename, dpi=150, bbox_inches=None):
        """
        Salva o gráfico atual e fecha a figura, liberando memória.
        """
        plt.tight_layout()
        save_kwargs = {"dpi": dpi}
        if bbox_inches:
            save_kwargs["bbox_inches"] = bbox_inches
        plt.savefig(f"{self.outputs_dir}/{filename}", **save_kwargs)
        plt.close()
