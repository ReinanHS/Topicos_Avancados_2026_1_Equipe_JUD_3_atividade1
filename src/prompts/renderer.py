from pathlib import Path

import jinja2


class PromptRenderer:
    """
    Encapsula a lógica de leitura e renderização de templates Jinja2
    a partir do diretório de prompts na raiz do projeto.
    """

    def __init__(self, prompts_root: Path = None):
        if prompts_root is None:
            self.prompts_root = Path(__file__).parent.parent.parent / "prompts"
        else:
            self.prompts_root = prompts_root

    def render(self, dataset_name: str, template_name: str, context: dict) -> str:
        """
        Renderiza um template localizado em `prompts/<dataset_name>/<template_name>`.

        Retorna string vazia caso o template não exista.
        """
        template_path = self.prompts_root / dataset_name / template_name

        if not template_path.exists():
            return ""

        with open(template_path, "r", encoding="utf-8") as f:
            template_str = f.read()

        template = jinja2.Template(template_str)
        return template.render(**context)

    def render_from_path(self, template_path: Path, context: dict) -> str:
        """
        Renderiza um template a partir de um caminho absoluto.

        Retorna string vazia caso o template não exista.
        """
        if not template_path.exists():
            return ""

        with open(template_path, "r", encoding="utf-8") as f:
            template_str = f.read()

        template = jinja2.Template(template_str)
        return template.render(**context)
