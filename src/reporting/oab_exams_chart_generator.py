import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from src.reporting.base_chart_generator import BaseChartGenerator


class OabExamsChartGenerator(BaseChartGenerator):
    """
    Especifica a geração de gráficos para o dataset oab_exams,
    focando em métricas exatas como Acurácia, Precisão, Recall e F1.
    """

    def generate_all_charts(self):
        print("Carregando arquivos de dados para oab_exams...")

        models = self.storage.list_available_models(self.dataset)
        if not models:
            print("Nenhum modelo encontrado para gerar gráficos do oab_exams.")
            return

        model_metrics = {}
        for model in models:
            filename = model.replace(":", "-")
            try:
                data = self.storage.load_data(
                    filename, fmt="json", sub_dir=f"results/{self.dataset}/model_metric"
                )
                if data and isinstance(data, list):
                    model_metrics[model] = data[0]
            except FileNotFoundError:
                print(f"Métricas não encontradas para o modelo {model}.")

        if not model_metrics:
            print("Nenhum dado de métrica pôde ser carregado.")
            return

        print("Iniciando a geração dos gráficos para oab_exams...")
        self._plot_bar_metrics(model_metrics)
        self._plot_radar_metrics(model_metrics)

        print(
            f"Todos os gráficos do oab_exams gerados com sucesso e salvos em {self.outputs_dir}"
        )

    def _plot_bar_metrics(self, model_metrics):
        fig, ax = plt.subplots(figsize=(10, 6))

        models = list(model_metrics.keys())

        metrics = ["accuracy", "precision", "recall", "f1"]
        metric_labels = ["Acurácia", "Precisão", "Recall", "F1 Score"]

        x = np.arange(len(models))
        width = 0.2
        colors = sns.color_palette("Set2", len(metrics))

        for i, (m, ml) in enumerate(zip(metrics, metric_labels)):
            vals = [model_metrics[mod].get(m, 0.0) for mod in models]
            bars = ax.bar(x + i * width, vals, width, label=ml, color=colors[i])
            for bar in bars:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.01,
                    f"{bar.get_height():.3f}",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )

        ax.set_xticks(x + width * 1.5)
        ax.set_xticklabels(models, fontsize=11)
        ax.set_ylabel("Score")
        ax.set_ylim(0, 1.1)
        ax.set_title(
            "Métricas de Avaliação Exata — Comparação entre Modelos",
            fontsize=13,
            fontweight="bold",
        )
        ax.legend(loc="upper right", fontsize=9)
        plt.tight_layout()
        plt.savefig(f"{self.outputs_dir}/01_barras_metricas_exatas.png", dpi=150)
        plt.close()
        print("✓ 01 Barras: Métricas Exatas")

    def _plot_radar_metrics(self, model_metrics):
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

        models = list(model_metrics.keys())
        metrics = ["accuracy", "precision", "recall", "f1"]
        metric_labels = ["Acurácia", "Precisão", "Recall", "F1 Score"]

        angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist() + [0]
        colors = sns.color_palette("Set1", len(models))

        for idx, model in enumerate(models):
            values = [model_metrics[model].get(m, 0.0) for m in metrics]
            values += [values[0]]

            ax.fill(angles, values, alpha=0.1, color=colors[idx])
            ax.plot(angles, values, "o-", color=colors[idx], linewidth=2, label=model)
            for a, v in zip(angles[:-1], values[:-1]):
                ax.annotate(f"{v:.3f}", xy=(a, v), fontsize=8, ha="center", va="bottom")

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metric_labels, fontsize=11, fontweight="bold")
        ax.set_ylim(0, 1.0)
        ax.set_title(
            "Desempenho Geral dos Modelos (Radar)",
            fontsize=14,
            fontweight="bold",
            pad=20,
        )
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))

        plt.tight_layout()
        plt.savefig(
            f"{self.outputs_dir}/02_radar_metricas_exatas.png",
            dpi=150,
            bbox_inches="tight",
        )
        plt.close()
        print("✓ 02 Radar: Métricas Exatas")
