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
        """
        Orquestra o carregamento dos dados e a geração de todos os gráficos.
        """
        print("Carregando arquivos de dados para oab_exams...")

        models = self.storage.list_available_models(self.dataset)
        if not models:
            print("Nenhum modelo encontrado para gerar gráficos do oab_exams.")
            return

        model_metrics = self._load_model_metrics(models)
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

    def _load_model_metrics(self, models):
        """
        Carrega as métricas de avaliação para cada modelo disponível.
        """
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
        return model_metrics

    def _load_answer_map(self):
        """
        Carrega o dataset original e constrói um mapa de respostas corretas.
        """
        dataset_items = self.storage.load_data(
            self.dataset, fmt="json", sub_dir="dataset"
        )
        answer_map = {}
        for item in dataset_items:
            q_id = item.get("id", item.get("question_id", ""))
            if q_id:
                answer_map[q_id] = item.get("answerKey", "")
        return answer_map

    def _load_curatorship_maps(self):
        """
        Carrega dados de curadoria e constrói mapas de dificuldade e área.
        """
        curatorship_items = self.storage.load_data(
            "gpt-4o-mini",
            fmt="json",
            sub_dir=f"results/{self.dataset}/model_curatorship",
        )
        difficulty_map = {}
        area_map = {}
        for item in curatorship_items:
            q_id = item.get("question_id", "")
            if not q_id:
                continue
            cur = item.get("curatorship", {})
            difficulty_map[q_id] = self._parse_difficulty(cur)
            area_map[q_id] = str(cur.get("area_expertise", "Variadas/Outros")).strip()
        return difficulty_map, area_map

    @staticmethod
    def _parse_difficulty(curatorship):
        """
        Converte o valor de dificuldade para inteiro, com fallback para 0.
        """
        try:
            return int(curatorship.get("difficulty_question", 0))
        except (ValueError, TypeError):
            return 0

    def _build_curatorship_stats(self, models, answer_map, difficulty_map, area_map):
        """
        Itera as respostas de cada modelo e contabiliza acertos por
        dificuldade e área de especialidade.
        """
        stats_diff = {model: {1: 0, 2: 0, 3: 0, "Outros/N/A": 0} for model in models}
        stats_area = {model: {} for model in models}

        for model in models:
            self._count_correct_answers(
                model, answer_map, difficulty_map, area_map, stats_diff, stats_area
            )
        return stats_diff, stats_area

    def _count_correct_answers(
        self, model, answer_map, difficulty_map, area_map, stats_diff, stats_area
    ):
        """
        Carrega as respostas de um modelo e contabiliza as corretas.
        """
        filename = model.replace(":", "-")
        try:
            answers = self.storage.load_data(
                filename,
                fmt="json",
                sub_dir=f"results/{self.dataset}/model_answer",
            )
        except FileNotFoundError:
            return

        for ans in answers:
            q_id = ans.get("question_id", "")
            obj_answer = self._extract_objective_answer(ans)
            if not obj_answer:
                continue

            correct_answer = answer_map.get(q_id)
            if not correct_answer or obj_answer != correct_answer:
                continue

            self._record_correct_answer(
                q_id, model, difficulty_map, area_map, stats_diff, stats_area
            )

    @staticmethod
    def _extract_objective_answer(answer_item):
        """
        Extrai a resposta objetiva de um item de resposta do modelo.
        """
        choices = answer_item.get("choices", [])
        if not choices:
            return ""
        return choices[0].get("objective_answer", "")

    @staticmethod
    def _record_correct_answer(
        q_id, model, difficulty_map, area_map, stats_diff, stats_area
    ):
        """
        Registra um acerto nos dicts de estatísticas por dificuldade e área.
        """
        diff = difficulty_map.get(q_id, 0)
        diff_key = diff if diff in (1, 2, 3) else "Outros/N/A"
        stats_diff[model][diff_key] += 1

        area = area_map.get(q_id, "Variadas/Outros")
        stats_area[model][area] = stats_area[model].get(area, 0) + 1

    def _generate_curatorship_charts(self, models):
        """
        Orquestra a geração dos gráficos baseados em curadoria.
        """
        try:
            answer_map = self._load_answer_map()
            difficulty_map, area_map = self._load_curatorship_maps()
            stats_diff, stats_area = self._build_curatorship_stats(
                models, answer_map, difficulty_map, area_map
            )
            self._plot_correct_by_difficulty(stats_diff)
            self._plot_correct_by_area(stats_area)
        except FileNotFoundError as e:
            print(
                f"Não foi possível gerar gráficos de curadoria (faltam arquivos base): {e}"
            )

    def _plot_bar_metrics(self, model_metrics):
        """Gráfico de barras agrupadas com métricas exatas de cada modelo."""
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
            self._add_bar_labels(ax, bars, fmt=".3f", fontsize=8, padding=0.01)

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
        self._save_and_close("01_barras_metricas_exatas.png")
        print("✓ 01 Barras: Métricas Exatas")

    def _plot_radar_metrics(self, model_metrics):
        """Gráfico radar com o perfil de métricas exatas de cada modelo."""
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
        self._save_and_close("02_radar_metricas_exatas.png", bbox_inches="tight")
        print("✓ 02 Radar: Métricas Exatas")

    def _plot_correct_by_difficulty(self, stats):
        """
        Gráfico de barras com acertos agrupados por nível de dificuldade.
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        models = list(stats.keys())
        difficulties = self._get_difficulty_categories(stats, models)
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
            self._add_bar_labels(ax, bars, fmt="d", fontsize=8, padding=0.1)

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
        self._save_and_close("03_barras_dificuldade_acertos.png")
        print("✓ 03 Barras: Acertos por Nível de Dificuldade")

    @staticmethod
    def _get_difficulty_categories(stats, models):
        """
        Determina quais categorias de dificuldade exibir no gráfico.
        """
        difficulties = [1, 2, 3]
        has_others = sum(stats[m]["Outros/N/A"] for m in models) > 0
        if has_others:
            difficulties.append("Outros/N/A")
        return difficulties

    def _plot_correct_by_area(self, stats_area):
        """
        Gráfico de barras horizontais com acertos por área de especialidade (Top 5).
        """
        models = list(stats_area.keys())
        all_areas = self._get_top_areas(stats_area, models, top_n=5)

        fig, ax = plt.subplots(figsize=(10, max(5, len(all_areas) * 0.5)))

        y = np.arange(len(all_areas))
        height = 0.8 / max(1, len(models))
        colors = sns.color_palette("Set2", len(models))

        for i, model in enumerate(models):
            vals = [stats_area[model].get(area, 0) for area in all_areas]
            offset = (i - len(models) / 2 + 0.5) * height
            bars = ax.barh(y + offset, vals, height, label=model, color=colors[i])
            self._add_barh_labels(ax, bars, fontsize=8, padding=0.1)

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
        self._save_and_close("04_barras_areas_acertos.png", bbox_inches="tight")
        print("✓ 04 Barras (Horizontal): Acertos por Área (Top 5)")

    @staticmethod
    def _get_top_areas(stats_area, models, top_n=5):
        """
        Seleciona as top N áreas de especialidade com mais acertos totais.
        """
        all_areas = set()
        for m in models:
            all_areas.update(stats_area[m].keys())

        area_totals = {
            area: sum(stats_area[m].get(area, 0) for m in models) for area in all_areas
        }
        top_areas = sorted(
            area_totals.keys(), key=lambda a: area_totals[a], reverse=True
        )[:top_n]
        top_areas.reverse()
        return top_areas
