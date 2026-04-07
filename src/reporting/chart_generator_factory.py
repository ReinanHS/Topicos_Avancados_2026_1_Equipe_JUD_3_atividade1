from src.reporting.base_chart_generator import BaseChartGenerator


class ChartGeneratorFactory:
    """
    Factory para criar o gerador de relatórios apropriado para cada dataset.
    """

    @staticmethod
    def create(dataset: str) -> BaseChartGenerator:
        if dataset == "oab_bench":
            from src.reporting.oab_bench_chart_generator import OabBenchChartGenerator

            return OabBenchChartGenerator(dataset)
        elif dataset == "oab_exams":
            from src.reporting.oab_exams_chart_generator import OabExamsChartGenerator

            return OabExamsChartGenerator(dataset)
        else:
            raise ValueError(
                f"Dataset '{dataset}' não possui um gerador de gráficos associado."
            )
