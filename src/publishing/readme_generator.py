import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


class ReadmeGenerator:
    """Gerencia a coleta de métricas e gráficos para compor o README via Jinja."""

    def __init__(self, cache_dir: str = ".reinan_cache"):
        self.cache_dir = Path(cache_dir).resolve()
        self.template_dir = Path(__file__).parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))

    def _load_json_file(self, filepath: Path) -> dict:
        """Carrega e parseia um arquivo JSON de métricas."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data[0]
                return data
        except Exception as e:
            print(f"Erro ao ler métrica {filepath.name}: {e}")
            return {}

    def _collect_metrics(self, dataset: str, use_rag: bool = False) -> dict:
        """Coleta as métricas em JSON retornando um dicionário indexado pelo nome do modelo (arquivo)."""
        metrics = {}
        suffix = "/rag" if use_rag else "/default"
        metrics_dir = self.cache_dir / "results" / dataset / f"model_metric{suffix}"

        if not metrics_dir.exists():
            # Fallback
            metrics_dir = self.cache_dir / "results" / dataset / "model_metric"

        if not metrics_dir.exists():
            return metrics

        for json_file in sorted(metrics_dir.glob("*.json")):
            metrics[json_file.stem] = self._load_json_file(json_file)

        return metrics

    def _collect_charts(self, dataset: str, use_rag: bool = False) -> list:
        """Retorna uma lista de caminhos relativos (em relação ao README.md) para as imagens criadas pelo dataset."""
        charts = []
        suffix = "rag" if use_rag else "default"
        charts_dir = self.cache_dir / "results" / dataset / "charts" / suffix

        if not charts_dir.exists():
            # Fallback
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

    def generate(
        self, output_filename: str = "README.md", use_rag: bool = False
    ) -> Path:
        """Executa a coleta de dados e converte o template jinja para o arquivo markdown final."""
        print("Coletando métricas e gráficos para o README...")

        oab_bench_metrics = self._collect_metrics("oab_bench", use_rag=use_rag)
        oab_bench_charts = self._collect_charts("oab_bench", use_rag=use_rag)

        oab_exams_metrics = self._collect_metrics("oab_exams", use_rag=use_rag)
        oab_exams_charts = self._collect_charts("oab_exams", use_rag=use_rag)

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
