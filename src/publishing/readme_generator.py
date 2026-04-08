import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


class ReadmeGenerator:
    """Gerencia a coleta de métricas e gráficos para compor o README via Jinja."""

    def __init__(self, cache_dir: str = ".reinan_cache"):
        self.cache_dir = Path(cache_dir).resolve()
        self.template_dir = Path(__file__).parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))

    def _collect_metrics(self, dataset: str) -> dict:
        """Coleta as métricas em JSON retornando um dicionário indexado pelo nome do modelo (arquivo)."""
        metrics = {}
        metrics_dir = self.cache_dir / "results" / dataset / "model_metric"

        if not metrics_dir.exists():
            return metrics

        for json_file in sorted(metrics_dir.glob("*.json")):
            model_name = json_file.stem
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        metrics[model_name] = data[0]
                    else:
                        metrics[model_name] = data
            except Exception as e:
                print(f"Erro ao ler métrica {json_file.name}: {e}")

        return metrics

    def _collect_charts(self, dataset: str) -> list:
        """Retorna uma lista de caminhos relativos (em relação ao README.md) para as imagens criadas pelo dataset."""
        charts = []
        charts_dir = self.cache_dir / "results" / dataset / "charts"

        if not charts_dir.exists():
            return charts

        for ext in ["*.png", "*.jpg", "*.svg"]:
            for img_path in sorted(charts_dir.glob(ext)):
                # Geração do percurso relativo ("results/.../...")
                rel_path = img_path.relative_to(self.cache_dir)
                # Conversão explícita para unix-style no markdown
                charts.append(str(rel_path).replace("\\", "/"))

        return charts

    def generate(self, output_filename: str = "README.md") -> Path:
        """Executa a coleta de dados e converte o template jinja para o arquivo markdown final."""
        print("Coletando métricas e gráficos para o README...")

        oab_bench_metrics = self._collect_metrics("oab_bench")
        oab_bench_charts = self._collect_charts("oab_bench")

        oab_exams_metrics = self._collect_metrics("oab_exams")
        oab_exams_charts = self._collect_charts("oab_exams")

        context = {
            "oab_bench_metrics": oab_bench_metrics,
            "oab_bench_charts": oab_bench_charts,
            "oab_exams_metrics": oab_exams_metrics,
            "oab_exams_charts": oab_exams_charts,
        }

        template = self.env.get_template("readme.md.jinja")
        rendered_content = template.render(**context)

        output_path = self.cache_dir / output_filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered_content)

        print(f"README gerado com sucesso em: {output_path}")
        return output_path
