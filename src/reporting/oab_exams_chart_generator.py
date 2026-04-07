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

        self._generate_curatorship_charts(models)

        print(
            f"Todos os gráficos do oab_exams gerados com sucesso e salvos em {self.outputs_dir}"
        )

    def _generate_curatorship_charts(self, models):
        """
        Contabiliza acertos por modelo, agrupando pela dificuldade e área de especialidade,
        avaliadas pela curadoria do gpt-4o-mini, e gera os gráficos.
        """
        try:
            dataset_items = self.storage.load_data(
                self.dataset, fmt="json", sub_dir="dataset"
            )

            answer_map = {}
            for item in dataset_items:
                q_id = item.get("id", item.get("question_id", ""))
                if q_id:
                    answer_map[q_id] = item.get("answerKey", "")

            curatorship_items = self.storage.load_data(
                "gpt-4o-mini",
                fmt="json",
                sub_dir=f"results/{self.dataset}/model_curatorship",
            )
            difficulty_map = {}
            area_map = {}
            for item in curatorship_items:
                q_id = item.get("question_id", "")
                cur = item.get("curatorship", {})
                diff = cur.get("difficulty_question", 0)
                area = cur.get("area_expertise", "Variadas/Outros")

                try:
                    diff = int(diff)
                except ValueError:
                    diff = 0
                if q_id:
                    difficulty_map[q_id] = diff
                    area_map[q_id] = str(area).strip()

            stats_diff = {
                model: {1: 0, 2: 0, 3: 0, "Outros/N/A": 0} for model in models
            }
            stats_area = {model: {} for model in models}

            for model in models:
                filename = model.replace(":", "-")
                try:
                    answers = self.storage.load_data(
                        filename,
                        fmt="json",
                        sub_dir=f"results/{self.dataset}/model_answer",
                    )
                    for ans in answers:
                        q_id = ans.get("question_id", "")
                        choices = ans.get("choices", [])
                        if not choices:
                            continue

                        obj_answer = choices[0].get("objective_answer", "")
                        correct_answer = answer_map.get(q_id, None)

                        if correct_answer and obj_answer == correct_answer:
                            diff = difficulty_map.get(q_id, 0)
                            if diff in [1, 2, 3]:
                                stats_diff[model][diff] += 1
                            else:
                                stats_diff[model]["Outros/N/A"] += 1

                            area = area_map.get(q_id, "Variadas/Outros")
                            stats_area[model][area] = stats_area[model].get(area, 0) + 1

                except FileNotFoundError:
                    pass

            self._plot_correct_by_difficulty(stats_diff)
            self._plot_correct_by_area(stats_area)

        except FileNotFoundError as e:
            print(
                f"Não foi possível gerar gráficos de curadoria (faltam arquivos base): {e}"
            )

    def _plot_correct_by_difficulty(self, stats):
        fig, ax = plt.subplots(figsize=(10, 6))

        models = list(stats.keys())
        difficulties = [1, 2, 3]

        has_others = sum(stats[m]["Outros/N/A"] for m in models) > 0
        if has_others:
            difficulties.append("Outros/N/A")

        label_map = {1: "Fácil", 2: "Médio", 3: "Difícil"}
        diff_labels = [label_map.get(d, d) for d in difficulties]

        x = np.arange(len(models))
        width = 0.2
        colors = sns.color_palette("Set2", len(difficulties))

        for i, d in enumerate(difficulties):
            vals = [stats[m].get(d, 0) for m in models]
            bars = ax.bar(
                x + i * width, vals, width, label=diff_labels[i], color=colors[i]
            )
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        height + 0.1,
                        f"{int(height)}",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                    )

        ax.set_xticks(x + width * (len(difficulties) - 1) / 2)
        ax.set_xticklabels(models, fontsize=11)
        ax.set_ylabel("Quantidade de Acertos")

        max_val = max([max([stats[m][d] for d in difficulties]) for m in models] + [10])
        ax.set_ylim(0, max_val * 1.2)

        ax.set_title(
            "Quantidade de Acertos por Nível de Dificuldade",
            fontsize=13,
            fontweight="bold",
        )
        ax.legend(title="Dificuldade", loc="upper right", fontsize=9)
        plt.tight_layout()
        plt.savefig(f"{self.outputs_dir}/03_barras_dificuldade_acertos.png", dpi=150)
        plt.close()
        print("✓ 03 Barras: Acertos por Nível de Dificuldade")

    def _plot_correct_by_area(self, stats_area):
        models = list(stats_area.keys())
        all_areas = set()
        for m in models:
            all_areas.update(stats_area[m].keys())

        area_totals = {
            area: sum(stats_area[m].get(area, 0) for m in models) for area in all_areas
        }

        top_areas = sorted(
            area_totals.keys(), key=lambda a: area_totals[a], reverse=True
        )[:5]

        top_areas.reverse()
        all_areas = top_areas

        fig, ax = plt.subplots(figsize=(10, max(5, len(all_areas) * 0.5)))

        y = np.arange(len(all_areas))
        height = 0.8 / max(1, len(models))
        colors = sns.color_palette("Set2", len(models))

        for i, model in enumerate(models):
            vals = [stats_area[model].get(area, 0) for area in all_areas]

            offset = (i - len(models) / 2 + 0.5) * height

            bars = ax.barh(y + offset, vals, height, label=model, color=colors[i])
            for bar in bars:
                width = bar.get_width()
                if width > 0:
                    ax.text(
                        width + 0.1,
                        bar.get_y() + bar.get_height() / 2,
                        f"{int(width)}",
                        ha="left",
                        va="center",
                        fontsize=8,
                    )

        ax.set_yticks(y)
        ax.set_yticklabels(all_areas, fontsize=10)
        ax.set_xlabel("Quantidade de Acertos")
        ax.set_title(
            "Acertos por Área de Especialidade (Top 5)",
            fontsize=13,
            fontweight="bold",
        )

        ax.legend(
            title="Modelos", loc="center left", bbox_to_anchor=(1, 0.5), fontsize=10
        )

        plt.tight_layout()
        plt.savefig(
            f"{self.outputs_dir}/04_barras_areas_acertos.png",
            dpi=150,
            bbox_inches="tight",
        )
        plt.close()
        print("✓ 04 Barras (Horizontal): Acertos por Área (Top 5)")

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
