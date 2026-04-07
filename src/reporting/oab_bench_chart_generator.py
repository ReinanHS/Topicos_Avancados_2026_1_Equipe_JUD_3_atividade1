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
        """
        Orquestra o carregamento dos dados e a geração de todos os gráficos.

        Refatoração: a lógica de carregamento e merge foi extraída
        para _load_all_pair_data() e _merge_pairs(), reduzindo a
        CC de ~14 para ~4.
        """
        print("Carregando arquivos de dados para oab_bench...")

        pair_data, judgment_data = self._load_all_pair_data()
        if pair_data is None:
            return

        all_pairs = self._merge_pairs(pair_data)
        metrics = ["bleu", "rouge1", "rouge2", "rougeL", "bertscore_f1"]
        metric_labels = ["BLEU", "ROUGE-1", "ROUGE-2", "ROUGE-L", "BERTScore F1"]

        model_pairs = [k for k in all_pairs if "guideline" not in k]
        guideline_pairs = [k for k in all_pairs if "guideline" in k]
        df_judge = pd.DataFrame(judgment_data)

        print("Iniciando a geração dos gráficos para oab_bench...")
        self._plot_heatmap_bertscore(all_pairs)
        self._plot_grouped_bar_chart(
            all_pairs,
            model_pairs,
            metrics,
            metric_labels,
            title="Métricas de Similaridade — Comparação entre Modelos",
            ylim=0.9,
            label_formatter=lambda p: p.replace(" vs ", "\nvs\n"),
            filename="02_barras_modelo_vs_modelo.png",
            log_label="02 Barras: Modelo vs Modelo",
        )
        self._plot_grouped_bar_chart(
            all_pairs,
            guideline_pairs,
            metrics,
            metric_labels,
            title="Aderência dos Modelos à Guideline de Referência",
            ylim=0.75,
            label_formatter=lambda p: p.replace(" vs guideline", ""),
            filename="03_barras_modelo_vs_guideline.png",
            log_label="03 Barras: Modelo vs Guideline",
            label_fontsize=11,
            padding=0.005,
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

    def _load_all_pair_data(self):
        """
        Carrega os dados de métricas dos 3 modelos e do judgment.
        """
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
                "qwen2.5-3b",
                fmt="json",
                sub_dir=f"results/{self.dataset}/model_metric",
            )[0]
            judgment_data = self.storage.load_data(
                "gpt-4o-mini",
                fmt="json",
                sub_dir=f"results/{self.dataset}/model_judgment",
            )
        except FileNotFoundError as e:
            print(f"Erro ao carregar os dados do oab_bench. Detalhes: {e}")
            return None, None

        return [gemma_data, llama_data, qwen_data], judgment_data

    @staticmethod
    def _merge_pairs(pair_data_list):
        """
        Consolida os dicts de pares de múltiplos modelos em um único dict.
        """
        all_pairs = {}
        for source in pair_data_list:
            for pair_name, pair_metrics in source.items():
                if pair_name not in all_pairs:
                    all_pairs[pair_name] = pair_metrics
        return all_pairs

    def _plot_heatmap_bertscore(self, all_pairs):
        """Heatmap de similaridade semântica (BERTScore F1) entre todos os pares."""
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
            "Similaridade semântica (BERTScore F1)\nMédia dos turns",
            fontsize=13,
            fontweight="bold",
        )
        self._save_and_close("01_heatmap_bertscore.png")
        print("✓ 01 Heatmap BERTScore F1")

    def _plot_grouped_bar_chart(
        self,
        all_pairs,
        pair_keys,
        metrics,
        metric_labels,
        title,
        ylim,
        label_formatter,
        filename,
        log_label,
        label_fontsize=10,
        padding=0.008,
    ):
        """
        Gráfico de barras agrupadas parametrizado
        para comparações modelo-vs-modelo e modelo-vs-guideline.
        """
        if not all(p in all_pairs for p in pair_keys):
            return

        fig, ax = plt.subplots(figsize=(12, 6))
        x = np.arange(len(pair_keys))
        width = 0.15
        colors = sns.color_palette("Set2", len(metrics))

        for i, (m, ml) in enumerate(zip(metrics, metric_labels)):
            vals = [all_pairs[p]["average"][m] for p in pair_keys]
            bars = ax.bar(x + i * width, vals, width, label=ml, color=colors[i])
            self._add_bar_labels(ax, bars, fmt=".3f", fontsize=7, padding=padding)

        ax.set_xticks(x + width * 2)
        ax.set_xticklabels(
            [label_formatter(p) for p in pair_keys], fontsize=label_fontsize
        )
        ax.set_ylabel("Score")
        ax.set_ylim(0, ylim)
        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.legend(loc="upper right", fontsize=9)
        self._save_and_close(filename)
        print(f"✓ {log_label}")

    def _plot_radar_model_vs_guideline(
        self, all_pairs, guideline_pairs, metrics, metric_labels
    ):
        """Radar chart comparando perfil de métricas de cada modelo vs guideline."""
        fig, axes = plt.subplots(1, 3, figsize=(16, 5), subplot_kw=dict(polar=True))
        rc = ["#e74c3c", "#3498db", "#2ecc71"]
        for idx, (pn, ax) in enumerate(zip(guideline_pairs, axes)):
            if pn not in all_pairs:
                continue
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
            "Perfil de métricas\nModelo vs Guideline",
            fontsize=14,
            fontweight="bold",
            y=1.02,
        )
        self._save_and_close("04_radar_modelo_vs_guideline.png", bbox_inches="tight")
        print("✓ 04 Radar: Modelo vs Guideline")

    def _plot_turn1_vs_turn2_bertscore(self, all_pairs):
        """Gráfico de barras comparando BERTScore F1 entre Turn 1 e Turn 2."""
        fig, ax = plt.subplots(figsize=(11, 6))
        apn = list(all_pairs.keys())
        x = np.arange(len(apn))
        w = 0.35
        t1 = [all_pairs[p]["turn_1"]["bertscore_f1"] for p in apn]
        t2 = [all_pairs[p]["turn_2"]["bertscore_f1"] for p in apn]
        b1 = ax.bar(x - w / 2, t1, w, label="Turn 1", color="#3498db")
        b2 = ax.bar(x + w / 2, t2, w, label="Turn 2", color="#e67e22")
        self._add_bar_labels(
            ax, list(b1) + list(b2), fmt=".3f", fontsize=7, padding=0.003
        )
        ax.set_xticks(x)
        ax.set_xticklabels([p.replace(" vs ", "\nvs\n") for p in apn], fontsize=8)
        ax.set_ylabel("BERTScore F1")
        ax.set_ylim(0.6, 0.8)
        ax.set_title(
            "BERTScore F1 por Turn — Todos os Pares", fontsize=13, fontweight="bold"
        )
        ax.legend()
        self._save_and_close("05_turn1_vs_turn2_bertscore.png")
        print("✓ 05 Turn 1 vs Turn 2: BERTScore F1")

    def _plot_judgment_average_score(self, df_judge):
        """Gráfico de barras com score médio por modelo (Juiz: GPT-4o-mini)."""
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
        self._save_and_close("06_judgment_score_medio.png")
        print("✓ 06 Judgment: Score Médio")

    def _plot_judgment_score_by_turn(self, df_judge):
        """Gráfico de barras com score médio por modelo e turn."""
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
        self._save_and_close("07_judgment_score_por_turn.png")
        print("✓ 07 Judgment: Score por Turn")

    def _plot_judgment_boxplot(self, df_judge):
        """Boxplot da distribuição de scores por modelo."""
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
        self._save_and_close("08_judgment_boxplot.png")
        print("✓ 08 Judgment: Boxplot de Distribuição")

    def _plot_judgment_heatmap_questions(self, df_judge):
        """Heatmap de scores por questão e modelo."""
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
        self._save_and_close("09_judgment_heatmap_questoes.png")
        print("✓ 09 Judgment: Heatmap por Questão")

    def _plot_correlation_bertscore_judgment(
        self, df_judge, all_pairs, guideline_pairs
    ):
        """Scatter plot da correlação entre BERTScore F1 e score do juiz."""
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
            if jm not in judge_means.index or om not in cross_bert:
                continue
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
        self._save_and_close("10_correlacao_bertscore_judgment.png")
        print("✓ 10 Correlação: BERTScore vs Judgment")
