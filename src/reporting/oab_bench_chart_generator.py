import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from src.reporting.base_chart_generator import BaseChartGenerator


class OabBenchChartGenerator(BaseChartGenerator):
    """
    Especifica a geração de gráficos para o dataset oab_bench,
    lidando com métricas cross-model (BERTScore, ROUGE) e Judgment.
    """

    def generate_all_charts(self):
        print("Carregando arquivos de dados para oab_bench...")

        try:
            gemma_data = self.storage.load_data(
                "gemma2-2b", fmt="json", sub_dir=f"results/{self.dataset}/model_metric"
            )[0]
            llama_data = self.storage.load_data(
                "llama3.2-3b",
                fmt="json",
                sub_dir=f"results/{self.dataset}/model_metric",
            )[0]
            qwen_data = self.storage.load_data(
                "qwen2.5-3b", fmt="json", sub_dir=f"results/{self.dataset}/model_metric"
            )[0]
            judgment_data = self.storage.load_data(
                "gpt-4o-mini",
                fmt="json",
                sub_dir=f"results/{self.dataset}/model_judgment",
            )
        except FileNotFoundError as e:
            print(f"Erro ao carregar os dados do oab_bench. Detalhes: {e}")
            return

        all_pairs = {}
        for source in [gemma_data, llama_data, qwen_data]:
            for pair_name, pair_metrics in source.items():
                if pair_name not in all_pairs:
                    all_pairs[pair_name] = pair_metrics

        metrics = ["bleu", "rouge1", "rouge2", "rougeL", "bertscore_f1"]
        metric_labels = ["BLEU", "ROUGE-1", "ROUGE-2", "ROUGE-L", "BERTScore F1"]

        model_pairs = [k for k in all_pairs if "guideline" not in k]
        guideline_pairs = [k for k in all_pairs if "guideline" in k]
        df_judge = pd.DataFrame(judgment_data)

        print("Iniciando a geração dos gráficos para oab_bench...")
        self._plot_heatmap_bertscore(all_pairs)
        self._plot_bar_model_vs_model(all_pairs, model_pairs, metrics, metric_labels)
        self._plot_bar_model_vs_guideline(
            all_pairs, guideline_pairs, metrics, metric_labels
        )
        self._plot_radar_model_vs_guideline(
            all_pairs, guideline_pairs, metrics, metric_labels
        )
        self._plot_turn1_vs_turn2_bertscore(all_pairs)
        self._plot_judgment_average_score(df_judge)
        self._plot_judgment_score_by_turn(df_judge)
        self._plot_judgment_boxplot(df_judge)
        self._plot_judgment_heatmap_questions(df_judge)
        self._plot_correlation_bertscore_judgment(df_judge, all_pairs, guideline_pairs)

        print(
            f"Todos os gráficos do oab_bench gerados com sucesso e salvos em {self.outputs_dir}"
        )

    def _plot_heatmap_bertscore(self, all_pairs):
        fig, ax = plt.subplots(figsize=(7, 6))
        labels = ["gemma2:2b", "llama3.2:3b", "qwen2.5:3b", "guideline"]
        n = len(labels)
        matrix = np.full((n, n), np.nan)
        pair_map = {
            ("gemma2:2b", "llama3.2:3b"): "gemma2:2b vs llama3.2:3b",
            ("gemma2:2b", "qwen2.5:3b"): "gemma2:2b vs qwen2.5:3b",
            ("llama3.2:3b", "qwen2.5:3b"): "llama3.2:3b vs qwen2.5:3b",
            ("gemma2:2b", "guideline"): "gemma2:2b vs guideline",
            ("llama3.2:3b", "guideline"): "llama3.2:3b vs guideline",
            ("qwen2.5:3b", "guideline"): "qwen2.5:3b vs guideline",
        }
        for (a, b), pn in pair_map.items():
            if pn in all_pairs:
                val = all_pairs[pn]["average"]["bertscore_f1"]
                i, j = labels.index(a), labels.index(b)
                matrix[i][j] = val
                matrix[j][i] = val

        mask = np.isnan(matrix)
        sns.heatmap(
            matrix,
            annot=True,
            fmt=".4f",
            cmap="YlOrRd",
            xticklabels=labels,
            yticklabels=labels,
            mask=mask,
            vmin=0.6,
            vmax=0.8,
            linewidths=1,
            linecolor="white",
            cbar_kws={"label": "BERTScore F1"},
            ax=ax,
        )
        for i in range(n):
            ax.text(
                i + 0.5,
                i + 0.5,
                "—",
                ha="center",
                va="center",
                fontsize=14,
                color="gray",
            )
        ax.set_title(
            "Similaridade Semântica (BERTScore F1)\nMédia dos Turns",
            fontsize=13,
            fontweight="bold",
        )
        plt.tight_layout()
        plt.savefig(f"{self.outputs_dir}/01_heatmap_bertscore.png", dpi=150)
        plt.close()
        print("✓ 01 Heatmap BERTScore F1")

    def _plot_bar_model_vs_model(self, all_pairs, model_pairs, metrics, metric_labels):
        fig, ax = plt.subplots(figsize=(12, 6))
        x = np.arange(len(model_pairs))
        width = 0.15
        colors = sns.color_palette("Set2", len(metrics))
        for i, (m, ml) in enumerate(zip(metrics, metric_labels)):
            if all(p in all_pairs for p in model_pairs):
                vals = [all_pairs[p]["average"][m] for p in model_pairs]
                bars = ax.bar(x + i * width, vals, width, label=ml, color=colors[i])
                for bar in bars:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.008,
                        f"{bar.get_height():.3f}",
                        ha="center",
                        va="bottom",
                        fontsize=7,
                    )
        ax.set_xticks(x + width * 2)
        ax.set_xticklabels(
            [p.replace(" vs ", "\nvs\n") for p in model_pairs], fontsize=10
        )
        ax.set_ylabel("Score")
        ax.set_ylim(0, 0.9)
        ax.set_title(
            "Métricas de Similaridade — Comparação entre Modelos",
            fontsize=13,
            fontweight="bold",
        )
        ax.legend(loc="upper right", fontsize=9)
        plt.tight_layout()
        plt.savefig(f"{self.outputs_dir}/02_barras_modelo_vs_modelo.png", dpi=150)
        plt.close()
        print("✓ 02 Barras: Modelo vs Modelo")

    def _plot_bar_model_vs_guideline(
        self, all_pairs, guideline_pairs, metrics, metric_labels
    ):
        fig, ax = plt.subplots(figsize=(12, 6))
        x = np.arange(len(guideline_pairs))
        width = 0.15
        colors = sns.color_palette("Set2", len(metrics))
        for i, (m, ml) in enumerate(zip(metrics, metric_labels)):
            if all(p in all_pairs for p in guideline_pairs):
                vals = [all_pairs[p]["average"][m] for p in guideline_pairs]
                bars = ax.bar(x + i * width, vals, width, label=ml, color=colors[i])
                for bar in bars:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.005,
                        f"{bar.get_height():.3f}",
                        ha="center",
                        va="bottom",
                        fontsize=7,
                    )
        ax.set_xticks(x + width * 2)
        ax.set_xticklabels(
            [p.replace(" vs guideline", "") for p in guideline_pairs], fontsize=11
        )
        ax.set_ylabel("Score")
        ax.set_ylim(0, 0.75)
        ax.set_title(
            "Aderência dos Modelos à Guideline de Referência",
            fontsize=13,
            fontweight="bold",
        )
        ax.legend(loc="upper right", fontsize=9)
        plt.tight_layout()
        plt.savefig(f"{self.outputs_dir}/03_barras_modelo_vs_guideline.png", dpi=150)
        plt.close()
        print("✓ 03 Barras: Modelo vs Guideline")

    def _plot_radar_model_vs_guideline(
        self, all_pairs, guideline_pairs, metrics, metric_labels
    ):
        fig, axes = plt.subplots(1, 3, figsize=(16, 5), subplot_kw=dict(polar=True))
        rc = ["#e74c3c", "#3498db", "#2ecc71"]
        for idx, (pn, ax) in enumerate(zip(guideline_pairs, axes)):
            if pn in all_pairs:
                values = [all_pairs[pn]["average"][m] for m in metrics] + [
                    all_pairs[pn]["average"][metrics[0]]
                ]
                angles = np.linspace(
                    0, 2 * np.pi, len(metrics), endpoint=False
                ).tolist() + [0]
                ax.fill(angles, values, alpha=0.25, color=rc[idx])
                ax.plot(angles, values, "o-", color=rc[idx], linewidth=2)
                ax.set_xticks(angles[:-1])
                ax.set_xticklabels(metric_labels, fontsize=9)
                ax.set_ylim(0, 0.75)
                ax.set_title(
                    pn.replace(" vs guideline", ""),
                    fontsize=12,
                    fontweight="bold",
                    pad=20,
                )
                for a, v in zip(angles[:-1], values[:-1]):
                    ax.annotate(
                        f"{v:.3f}", xy=(a, v), fontsize=7.5, ha="center", va="bottom"
                    )
        fig.suptitle(
            "Perfil de Métricas — Modelo vs Guideline",
            fontsize=14,
            fontweight="bold",
            y=1.02,
        )
        plt.tight_layout()
        plt.savefig(
            f"{self.outputs_dir}/04_radar_modelo_vs_guideline.png",
            dpi=150,
            bbox_inches="tight",
        )
        plt.close()
        print("✓ 04 Radar: Modelo vs Guideline")

    def _plot_turn1_vs_turn2_bertscore(self, all_pairs):
        fig, ax = plt.subplots(figsize=(11, 6))
        apn = list(all_pairs.keys())
        x = np.arange(len(apn))
        w = 0.35
        t1 = [all_pairs[p]["turn_1"]["bertscore_f1"] for p in apn]
        t2 = [all_pairs[p]["turn_2"]["bertscore_f1"] for p in apn]
        b1 = ax.bar(x - w / 2, t1, w, label="Turn 1", color="#3498db")
        b2 = ax.bar(x + w / 2, t2, w, label="Turn 2", color="#e67e22")
        for bar in list(b1) + list(b2):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.003,
                f"{bar.get_height():.3f}",
                ha="center",
                va="bottom",
                fontsize=7,
            )
        ax.set_xticks(x)
        ax.set_xticklabels([p.replace(" vs ", "\nvs\n") for p in apn], fontsize=8)
        ax.set_ylabel("BERTScore F1")
        ax.set_ylim(0.6, 0.8)
        ax.set_title(
            "BERTScore F1 por Turn — Todos os Pares", fontsize=13, fontweight="bold"
        )
        ax.legend()
        plt.tight_layout()
        plt.savefig(f"{self.outputs_dir}/05_turn1_vs_turn2_bertscore.png", dpi=150)
        plt.close()
        print("✓ 05 Turn 1 vs Turn 2: BERTScore F1")

    def _plot_judgment_average_score(self, df_judge):
        fig, ax = plt.subplots(figsize=(8, 5))
        ms = df_judge.groupby("model")["score"].mean().sort_values(ascending=False)
        bc = ["#2ecc71", "#3498db", "#e74c3c", "#f1c40f", "#9b59b6"]
        bars = ax.bar(
            ms.index, ms.values, color=bc[: len(ms)], edgecolor="white", linewidth=1.5
        )
        for bar, val in zip(bars, ms.values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.005,
                f"{val:.3f}",
                ha="center",
                va="bottom",
                fontsize=12,
                fontweight="bold",
            )
        ax.set_ylabel("Score Médio")
        ax.set_title(
            "Score Médio por Modelo (Juiz: GPT-4o-mini)", fontsize=13, fontweight="bold"
        )
        ax.set_ylim(0, max(ms.values) * 1.25)
        plt.tight_layout()
        plt.savefig(f"{self.outputs_dir}/06_judgment_score_medio.png", dpi=150)
        plt.close()
        print("✓ 06 Judgment: Score Médio")

    def _plot_judgment_score_by_turn(self, df_judge):
        fig, ax = plt.subplots(figsize=(9, 5))
        pivot = df_judge.groupby(["model", "turn"])["score"].mean().unstack()
        pivot.plot(
            kind="bar",
            ax=ax,
            color=["#3498db", "#e67e22"],
            edgecolor="white",
            linewidth=1,
        )
        ax.set_ylabel("Score Médio")
        ax.set_title(
            "Score Médio por Modelo e Turn (Juiz: GPT-4o-mini)",
            fontsize=13,
            fontweight="bold",
        )
        ax.legend(["Turn 1", "Turn 2"], title="Turn")
        ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
        for c in ax.containers:
            ax.bar_label(c, fmt="%.3f", fontsize=9, padding=3)
        ax.set_ylim(0, max(df_judge.groupby(["model", "turn"])["score"].mean()) * 1.35)
        plt.tight_layout()
        plt.savefig(f"{self.outputs_dir}/07_judgment_score_por_turn.png", dpi=150)
        plt.close()
        print("✓ 07 Judgment: Score por Turn")

    def _plot_judgment_boxplot(self, df_judge):
        fig, ax = plt.subplots(figsize=(9, 5))
        sns.boxplot(
            data=df_judge,
            x="model",
            y="score",
            hue="model",
            palette="Set2",
            ax=ax,
            width=0.5,
            legend=False,
        )
        sns.stripplot(
            data=df_judge,
            x="model",
            y="score",
            color="black",
            alpha=0.4,
            size=4,
            ax=ax,
            jitter=True,
        )
        ax.set_ylabel("Score")
        ax.set_xlabel("Modelo")
        ax.set_title(
            "Distribuição dos Scores por Modelo (Juiz: GPT-4o-mini)",
            fontsize=13,
            fontweight="bold",
        )
        plt.tight_layout()
        plt.savefig(f"{self.outputs_dir}/08_judgment_boxplot.png", dpi=150)
        plt.close()
        print("✓ 08 Judgment: Boxplot de Distribuição")

    def _plot_judgment_heatmap_questions(self, df_judge):
        fig, ax = plt.subplots(figsize=(14, 7))
        sp = (
            df_judge.groupby(["question_id", "model"])["score"]
            .sum()
            .unstack(fill_value=0)
        )
        sp.index = [str(q).replace("44_", "").replace("_", " ") for q in sp.index]
        sns.heatmap(
            sp,
            annot=True,
            fmt=".2f",
            cmap="RdYlGn",
            linewidths=0.5,
            linecolor="white",
            ax=ax,
            cbar_kws={"label": "Score Total (Turn 1 + Turn 2)"},
        )
        ax.set_title(
            "Scores por Questão e Modelo (Juiz: GPT-4o-mini)",
            fontsize=13,
            fontweight="bold",
        )
        ax.set_ylabel("")
        ax.set_xlabel("Modelo")
        plt.tight_layout()
        plt.savefig(f"{self.outputs_dir}/09_judgment_heatmap_questoes.png", dpi=150)
        plt.close()
        print("✓ 09 Judgment: Heatmap por Questão")

    def _plot_correlation_bertscore_judgment(
        self, df_judge, all_pairs, guideline_pairs
    ):
        fig, ax = plt.subplots(figsize=(9, 5))
        model_name_map = {
            "gemma2-2b": "gemma2:2b",
            "llama3.2-3b": "llama3.2:3b",
            "qwen2.5-3b": "qwen2.5:3b",
        }
        judge_means = df_judge.groupby("model")["score"].mean()
        cross_bert = {
            p.replace(" vs guideline", ""): all_pairs[p]["average"]["bertscore_f1"]
            for p in guideline_pairs
            if p in all_pairs
        }
        sc = ["#e74c3c", "#3498db", "#2ecc71"]
        for idx, (jm, om) in enumerate(model_name_map.items()):
            if jm in judge_means.index and om in cross_bert:
                ax.scatter(
                    cross_bert[om],
                    judge_means[jm],
                    s=200,
                    color=sc[idx],
                    zorder=5,
                    edgecolors="black",
                )
                ax.annotate(
                    om,
                    (cross_bert[om], judge_means[jm]),
                    textcoords="offset points",
                    xytext=(10, 10),
                    fontsize=11,
                    fontweight="bold",
                )
        ax.set_xlabel("BERTScore F1 vs Guideline")
        ax.set_ylabel("Score Médio do Juiz (GPT-4o-mini)")
        ax.set_title(
            "Correlação: Similaridade com Guideline vs Nota do Juiz",
            fontsize=13,
            fontweight="bold",
        )
        plt.tight_layout()
        plt.savefig(f"{self.outputs_dir}/10_correlacao_bertscore_judgment.png", dpi=150)
        plt.close()
        print("✓ 10 Correlação: BERTScore vs Judgment")
