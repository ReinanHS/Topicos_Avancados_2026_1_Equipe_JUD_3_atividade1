import shutil
import subprocess
import tempfile
from pathlib import Path


class ResultsPublisher:
    """Gerencia a publicação de resultados estáticos em uma branch específica do Git."""

    def __init__(self, repo_url: str, branch: str, src_dir: str, exclude_dir: str):
        self.repo_url = repo_url
        self.branch = branch
        self.src_dir = Path(src_dir).resolve()
        self.exclude_dir = exclude_dir

    def _run_cmd(
        self, cmd: list, cwd: Path = None, check: bool = True
    ) -> subprocess.CompletedProcess:
        """Executa um comando no terminal e retorna o resultado."""
        print(f"Executando: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, cwd=cwd, check=check, text=True, capture_output=True
        )

        if result.stdout:
            print(result.stdout.strip())
        if result.returncode != 0 and not check:
            print(f"Aviso: O comando falhou com código {result.returncode}")
            if result.stderr:
                print(result.stderr.strip())

        return result

    def _clear_workspace(self, workdir_path: Path) -> None:
        """Limpa o diretório de trabalho, mantendo apenas a pasta .git."""
        self._run_cmd(["git", "rm", "-rf", "."], cwd=workdir_path, check=False)
        for item in workdir_path.iterdir():
            if item.name == ".git":
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    def _ignore_dataset(self, dir_path: str, contents: list) -> list:
        """Função para ignorar subdiretórios específicos durante a cópia."""
        if Path(dir_path) == self.src_dir and self.exclude_dir in contents:
            return [self.exclude_dir]
        return []

    def publish(self) -> None:
        """Executa o pipeline de publicação."""
        if not self.src_dir.exists():
            raise FileNotFoundError(
                f"Erro: O diretório de origem '{self.src_dir}' não existe."
            )

        with tempfile.TemporaryDirectory() as workdir:
            workdir_path = Path(workdir)

            self._run_cmd(["git", "clone", self.repo_url, str(workdir_path)])
            self._run_cmd(
                ["git", "checkout", "--orphan", self.branch], cwd=workdir_path
            )

            self._clear_workspace(workdir_path)

            shutil.copytree(
                self.src_dir,
                workdir_path,
                ignore=self._ignore_dataset,
                dirs_exist_ok=True,
            )
            print(
                f"\nArquivos de '{self.src_dir.name}' copiados (ignorando '{self.exclude_dir}')."
            )

            self._run_cmd(["git", "add", "."], cwd=workdir_path)

            commit_res = self._run_cmd(
                ["git", "commit", "-m", "feat: atualiza resultados estáticos"],
                cwd=workdir_path,
                check=False,
            )

            if commit_res.returncode != 0:
                print("\nNenhuma alteração detectada. Encerrando sem modificações.")
                return

            print(f"\nEnviando arquivos para a branch '{self.branch}' remotamente...")
            self._run_cmd(
                ["git", "push", "origin", self.branch, "--force"], cwd=workdir_path
            )
            print("\n======== Publicação concluída com sucesso! ========")
