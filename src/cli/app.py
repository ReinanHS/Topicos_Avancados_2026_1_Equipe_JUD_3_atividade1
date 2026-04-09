"""
Módulo CLI principal — interface de linha de comando baseada em Typer.

Cada comando delega sua lógica pesada para funções auxiliares privadas,
mantendo a complexidade cognitiva de cada função ≤ 12 (regra S3776 SonarCloud).
"""

import typer

app = typer.Typer(no_args_is_help=True)


def _validate_dataset(dataset: str) -> None:
    """Valida se o dataset informado é reconhecido pelo sistema."""
    from src.datasets.loader_factory import DatasetLoaderFactory

    if dataset not in DatasetLoaderFactory.available_datasets():
        typer.echo(
            f"Erro: Dataset '{dataset}' não reconhecido. "
            f"Use: {', '.join(DatasetLoaderFactory.available_datasets())}.",
            err=True,
        )
        raise typer.Exit(code=1)


def _validate_minimum_models(models: list, min_count: int, dataset: str) -> None:
    """Valida se há quantidade mínima de modelos disponíveis."""
    if len(models) >= min_count:
        return

    typer.echo(
        f"Foram encontrados resultados para apenas {len(models)} modelo(s): {models}."
    )
    typer.echo(
        f"Erro: São necessários no mínimo {min_count} modelo(s) com resultados salvos.",
        err=True,
    )
    typer.echo(
        f"Sugestão: Execute 'uv run python main.py infer {dataset} --model <nome_do_modelo>' "
        "para novos modelos."
    )
    raise typer.Exit(code=1)


def _display_cross_scores(cross_scores: dict) -> None:
    """Exibe os resultados da avaliação cruzada formatados no terminal."""
    typer.echo("\n--- Resultados da Avaliação Cruzada ---")
    for pair, scores in cross_scores.items():
        typer.echo(f"\n[{pair}]")
        for section, metrics in scores.items():
            typer.echo(f"  {section.upper()}:")
            for metric, value in metrics.items():
                typer.echo(f"    {metric.upper()}: {value:.4f}")


def _save_cross_model_metrics(
    storage, models: list, cross_scores: dict, dataset: str
) -> None:
    """Salva as métricas cruzadas de cada modelo em arquivo JSON."""
    for model in models:
        model_metrics = {
            pair: scores for pair, scores in cross_scores.items() if model in pair
        }
        filename = model.replace(":", "-")
        output_path = storage.save_data(
            [model_metrics],
            filename,
            fmt="json",
            sub_dir=f"results/{dataset}/model_metric",
        )
        typer.echo(f"Métricas de {model} salvas em: {output_path}")


def _evaluate_oab_bench(storage, models: list, dataset: str) -> None:
    """Orquestra a avaliação cruzada (pairwise) para o dataset oab_bench."""
    from src.evaluation.cross_model_evaluator import CrossModelEvaluator

    _validate_minimum_models(models, min_count=2, dataset=dataset)

    typer.echo(f"Modelos encontrados ({len(models)}): {', '.join(models)}")
    typer.echo("Iniciando a avaliação cruzada (Pairwise Metrics)...")

    try:
        evaluator = CrossModelEvaluator(storage)
        cross_scores = evaluator.evaluate(dataset, models)
        _display_cross_scores(cross_scores)
        _save_cross_model_metrics(storage, models, cross_scores, dataset)
    except Exception as e:
        typer.echo(f"Erro durante a avaliação: {e}", err=True)
        raise typer.Exit(code=1)


def _display_exact_scores(model_scores: dict) -> None:
    """Exibe os resultados da avaliação exata formatados no terminal."""
    typer.echo("\n--- Resultados da Avaliação ---")
    for mod, scores in model_scores.items():
        typer.echo(f"\n[{mod}]")
        for metric, score in scores.items():
            typer.echo(f"  {metric.upper()}: {score:.4f}")


def _save_exact_metrics(storage, model_scores: dict, dataset: str) -> None:
    """Salva as métricas de avaliação exata de cada modelo em arquivo JSON."""
    for mod, scores in model_scores.items():
        filename = mod.replace(":", "-")
        output_path = storage.save_data(
            [scores],
            filename,
            fmt="json",
            sub_dir=f"results/{dataset}/model_metric",
        )
        typer.echo(f"Métricas de {mod} salvas em: {output_path}")


def _evaluate_oab_exams(storage, models: list, dataset: str) -> None:
    """Orquestra a avaliação exata para o dataset oab_exams."""
    from src.evaluation.exact_match_evaluator import ExactMatchEvaluator

    _validate_minimum_models(models, min_count=1, dataset=dataset)

    typer.echo(f"Modelos encontrados ({len(models)}): {', '.join(models)}")
    typer.echo("Iniciando a avaliação exata (Acurácia, Precisão, Recall, F1)...")

    try:
        evaluator = ExactMatchEvaluator(storage)
        model_scores = evaluator.evaluate(dataset, models)
        _display_exact_scores(model_scores)
        _save_exact_metrics(storage, model_scores, dataset)
    except Exception as e:
        typer.echo(f"Erro durante a avaliação: {e}", err=True)
        raise typer.Exit(code=1)


def _resolve_models_to_judge(available_models: list, requested_model: str) -> list:
    """Resolve a lista de modelos a serem julgados."""
    if not available_models:
        typer.echo(
            "Erro: Nenhum modelo encontrado com respostas salvas. "
            "Execute o comando 'infer' primeiro para gerar os resultados.",
            err=True,
        )
        raise typer.Exit(code=1)

    if not requested_model:
        return available_models

    if requested_model not in available_models:
        typer.echo(
            f"Erro: Respostas para o modelo '{requested_model}' não foram encontradas.",
            err=True,
        )
        raise typer.Exit(code=1)

    return [requested_model]


def _process_model_judgments(
    judge_manager,
    models_to_run: list,
    dataset: str,
    limit,
    q_map: dict,
    ref_map: dict,
) -> list:
    """Processa os julgamentos para cada modelo, exibindo barra de progresso."""
    all_judgments = []

    for current_model in models_to_run:
        typer.echo(f"\nCarregando respostas do modelo {current_model}...")
        answers = judge_manager.load_model_answers(dataset, current_model)
        if limit is not None:
            answers = answers[:limit]

        typer.echo(f"Iniciando julgamento de {len(answers)} questões...")

        with typer.progressbar(
            answers, label=f"Julgando ({current_model})"
        ) as progress:
            for answer in progress:
                judgments = judge_manager.process_answer(
                    answer, current_model, q_map, ref_map
                )
                all_judgments.extend(judgments)

    return all_judgments


@app.callback()
def main_callback():
    """
    CLI para manipulação de datasets da OAB.
    """
    pass


@app.command()
def pull(
    dataset: str = typer.Argument(
        ..., help="Nome do dataset para baixar (ex: oab_bench, oab_exams)"
    ),
    output: str = typer.Option(
        "json", "--output", help="Formato do arquivo de saída (json ou csv)"
    ),
):
    """
    Baixa as informações do dataset e salva no diretório de armazenamento local em JSON ou CSV.
    """
    from src.datasets.loader_factory import DatasetLoaderFactory
    from src.storage.local_storage import LocalStorage

    loader = DatasetLoaderFactory.create(dataset)
    storage = LocalStorage()

    questions = loader.load_questions()

    caminho_arquivo = storage.save_data(
        questions, dataset, fmt=output, sub_dir="dataset"
    )

    typer.echo(f"Foram selecionadas {len(questions)} questões para o lote.")
    typer.echo(f"Conjunto de dados salvo com sucesso em: {caminho_arquivo}")


@app.command()
def infer(
    dataset: str = typer.Argument(
        ..., help="Nome do dataset para processar (ex: oab_bench, oab_exams)"
    ),
    model: str = typer.Option(
        None,
        "--model",
        "-m",
        help="Modelo do ollama para execução. Se não informado, executa para todos os modelos disponíveis.",
    ),
    limit: int = typer.Option(
        None,
        "--limit",
        "-l",
        help="Limitar a quantidade de questões a serem executadas.",
    ),
):
    """
    Executa a inferência e a classificação de dificuldade nas questões do dataset através do LLM local.
    """
    from src.execution.executor_factory import ExecutionManagerFactory
    from src.datasets.loader_factory import DatasetLoaderFactory
    from src.llm.ollama_client import OllamaClient
    from src.storage.local_storage import LocalStorage

    _validate_dataset(dataset)

    if model is not None and model not in OllamaClient.AVAILABLE_MODELS:
        typer.echo(
            f"Erro: Modelo '{model}' não é suportado pelo nosso OllamaClient.",
            err=True,
        )
        raise typer.Exit(code=1)

    models_to_run = [model] if model else OllamaClient.AVAILABLE_MODELS

    ollama_client = OllamaClient()
    loader = DatasetLoaderFactory.create(dataset)
    storage = LocalStorage()
    execution_manager = ExecutionManagerFactory.create(
        dataset, loader, storage, ollama_client
    )

    questions = execution_manager.get_questions(limit)

    import time

    for i, current_model in enumerate(models_to_run):
        if i > 0:
            typer.echo(
                "\nAguardando 15 segundos para limpeza de VRAM e estabilização do Ollama..."
            )
            time.sleep(15)

        typer.echo(
            f"\nIniciando a execução de {len(questions)} questões no modelo {current_model}..."
        )
        results = []

        with typer.progressbar(
            questions, label=f"Processando ({current_model})"
        ) as progress:
            for q in progress:
                q_result = execution_manager.process_full_question(q, current_model)
                results.append(q_result)

        output_path = execution_manager.save_results(results, current_model)

        typer.echo(
            f"Modelo {current_model} finalizado! Resultados salvos em: {output_path}"
        )

    typer.echo("\nExecução finalizada com sucesso!")


@app.command()
def evaluate(
    dataset: str = typer.Argument(
        ..., help="Nome do dataset para avaliar o resultado dos modelos."
    ),
):
    """Avalia as respostas geradas comparando-as de forma cruzada ou exata."""
    from src.storage.local_storage import LocalStorage

    _validate_dataset(dataset)

    storage = LocalStorage()

    typer.echo(f"Buscando modelos disponíveis para o dataset {dataset}...")
    models = storage.list_available_models(dataset)

    evaluator_map = {
        "oab_bench": _evaluate_oab_bench,
        "oab_exams": _evaluate_oab_exams,
    }

    evaluator_fn = evaluator_map.get(dataset)
    if not evaluator_fn:
        typer.echo(
            f"Erro: Avaliação não implementada para o dataset '{dataset}'.",
            err=True,
        )
        raise typer.Exit(code=1)

    evaluator_fn(storage, models, dataset)


@app.command()
def judgment(
    dataset: str = typer.Argument(
        ..., help="Nome do dataset para julgar (somente oab_bench)."
    ),
    judge: str = typer.Option(
        None,
        "--judge",
        "-j",
        help="Modelo a ser utilizado como juiz. Padrão: gpt-5.2.",
    ),
    model: str = typer.Option(
        None,
        "--model",
        "-m",
        help="Modelo do qual as respostas serão julgadas. Se não informado, executa para todos.",
    ),
    limit: int = typer.Option(
        None,
        "--limit",
        "-l",
        help="Limitar a quantidade de respostas a serem julgadas por modelo.",
    ),
):
    """
    Gera registros de julgamento (LLM as a Judge) para as respostas dos modelos.
    Disponível apenas para o dataset oab_bench.
    """
    from src.judgment.judge_manager import DEFAULT_JUDGE_MODEL, JudgeManager
    from src.storage.local_storage import LocalStorage

    if dataset != "oab_bench":
        typer.echo(
            f"Erro: O comando 'judgment' está disponível apenas para o dataset 'oab_bench'. "
            f"Dataset informado: '{dataset}'.",
            err=True,
        )
        raise typer.Exit(code=1)

    storage = LocalStorage()

    typer.echo(f"Buscando modelos disponíveis para o dataset {dataset}...")
    models = storage.list_available_models(dataset)

    models_to_run = _resolve_models_to_judge(models, model)

    judge_model = judge if judge else DEFAULT_JUDGE_MODEL
    judge_manager = JudgeManager(storage, judge_model=judge_model)

    typer.echo(
        f"Modelos selecionados ({len(models_to_run)}): {', '.join(models_to_run)}"
    )
    typer.echo(f"Modelo juiz: {judge_model}")

    try:
        q_map, ref_map = judge_manager.prepare_dataset_context(dataset)
        all_judgments = _process_model_judgments(
            judge_manager, models_to_run, dataset, limit, q_map, ref_map
        )
        output_path = judge_manager.save_judgments(dataset, all_judgments)
        typer.echo(f"\nJulgamentos salvos com sucesso em: {output_path}")
    except Exception as e:
        typer.echo(f"\nErro durante o julgamento: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def curate(
    dataset: str = typer.Argument(
        ..., help="Nome do dataset para curadoria (ex: oab_bench)"
    ),
    judge: str = typer.Option(
        "gpt-4o-mini",
        "--judge",
        "-j",
        help="Modelo a ser utilizado como curador (juiz). Padrão: gpt-4o-mini.",
    ),
    limit: int = typer.Option(
        None,
        "--limit",
        "-l",
        help="Limitar a quantidade de questões a serem analisadas pelo curador.",
    ),
):
    """
    Gera informações base de curadoria (dificuldade, legislação e área)
    para as questões do dataset, utilizando um modelo juiz LLM.
    """
    import time

    from src.datasets.loader_factory import DatasetLoaderFactory
    from src.execution.executor_factory import ExecutionManagerFactory
    from src.llm.openai_client import OpenAIClient
    from src.storage.local_storage import LocalStorage

    _validate_dataset(dataset)

    storage = LocalStorage()
    loader = DatasetLoaderFactory.create(dataset)

    llm_client = OpenAIClient()
    if judge not in llm_client.AVAILABLE_MODELS:
        llm_client.AVAILABLE_MODELS.append(judge)

    execution_manager = ExecutionManagerFactory.create(
        dataset, loader, storage, llm_client
    )

    questions = execution_manager.get_questions(limit)

    typer.echo(
        f"\nIniciando curadoria de {len(questions)} questões usando o juiz {judge}..."
    )
    records = []

    with typer.progressbar(questions, label=f"Curadoria ({judge})") as progress:
        for q in progress:
            difficulty_result = execution_manager.classify_difficulty(q, judge)
            legislation_result = execution_manager.define_basic_legislation(q, judge)
            area_result = execution_manager.define_area_expertise(q, judge)

            record = {
                "question_id": q.get("question_id", q.get("id", "")),
                "judge": judge,
                "curatorship": {
                    "difficulty_question": difficulty_result.get(
                        "difficulty_question", "Inconclusivo"
                    ),
                    "basic_legislation": legislation_result.get(
                        "basic_legislation", "Inconclusivo"
                    ),
                    "area_expertise": area_result.get("area_expertise", "Inconclusivo"),
                },
                "tstamp": time.time(),
            }
            records.append(record)

    filename = judge.replace(":", "-")
    sub_dir_name = "model_curatorship"

    output_path = storage.save_data(
        records,
        filename,
        fmt="json",
        sub_dir=f"results/{dataset}/{sub_dir_name}",
    )

    typer.echo(
        f"\nCuradoria com {judge} finalizada! Resultados salvos em: {output_path}"
    )


@app.command()
def report(
    dataset: str = typer.Argument(
        "oab_bench", help="Nome do dataset para o qual gerar o relatório."
    ),
):
    """
    Processa os resultados e gera diversos gráficos de métricas.
    """
    from src.reporting.chart_generator_factory import ChartGeneratorFactory

    typer.echo(f"Inicializando a geração de relatórios e gráficos para {dataset}...")

    try:
        generator = ChartGeneratorFactory.create(dataset)
        generator.generate_all_charts()
        typer.echo("Operação concluída com sucesso!")
    except Exception as e:
        typer.echo(f"Erro durante a geração dos gráficos: {e}", err=True)
        raise typer.Exit(code=1)


@app.command(name="build-readme")
def build_readme():
    """
    Gera o arquivo README.md consolidado das execuções dentro da pasta .reinan_cache.
    Este arquivo será publicado na branch de visualização dos resultados.
    """
    from src.publishing.readme_generator import ReadmeGenerator

    try:
        generator = ReadmeGenerator()
        generator.generate()
    except Exception as e:
        typer.echo(f"Erro durante a geração do README.md: {e}", err=True)
        raise typer.Exit(code=1)


def _publish_results(branch: str) -> None:
    """Orquestra a publicação dos resultados em uma branch externa."""
    from src.publishing.publisher import ResultsPublisher

    publisher = ResultsPublisher(
        repo_url="https://github.com/ReinanHS/Topicos_Avancados_2026_1_Equipe_JUD_3_atividade1.git",
        branch=branch,
        src_dir=".reinan_cache",
        exclude_dir="dataset",
    )

    try:
        publisher.publish()
    except Exception as e:
        typer.echo(f"Erro durante a publicação: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def publish(
    branch: str = typer.Option(
        "results",
        "--branch",
        "-b",
        help="Nome da branch de destino onde os arquivos estáticos serão publicados.",
    ),
):
    """
    Publica os resultados estáticos (pasta '.reinan_cache', exceto o 'dataset') em uma branch separada (ex: gh-pages).
    """
    typer.echo(f"Iniciando publicação de resultados na branch '{branch}'...")
    _publish_results(branch)


@app.command("run-all")
def run_all(
    limit: int = typer.Option(
        None,
        "--limit",
        "-l",
        help="Limitar a quantidade de questões a serem executadas no comando infer.",
    ),
    judge: str = typer.Option(
        "gpt-4o-mini",
        "--judge",
        "-j",
        help="Modelo a ser utilizado como curador (juiz). Padrão: gpt-4o-mini.",
    ),
):
    """
    Executa o fluxo completo do pipeline para os datasets:
    - pull oab_bench
    - pull oab_exams
    - infer oab_bench
    - infer oab_exams
    - evaluate oab_bench
    - evaluate oab_exams
    - judgment oab_bench
    - curate oab_bench
    - curate oab_exams
    - report oab_bench
    - report oab_exams
    - build-readme
    """
    import time

    start_time = time.time()

    typer.echo("=== Iniciando execução do pipeline completo ===")

    typer.echo("\n[01/12] Executando 'pull' para 'oab_bench'...")
    pull(dataset="oab_bench", output="json")

    typer.echo("\n[02/12] Executando 'pull' para 'oab_exams'...")
    pull(dataset="oab_exams", output="json")

    typer.echo("\n[03/12] Executando 'infer' para 'oab_bench'...")
    infer(dataset="oab_bench", model=None, limit=limit)

    typer.echo("\n[04/12] Executando 'infer' para 'oab_exams'...")
    infer(dataset="oab_exams", model=None, limit=limit)

    typer.echo("\n[05/12] Executando 'evaluate' para 'oab_bench'...")
    evaluate(dataset="oab_bench")

    typer.echo("\n[06/12] Executando 'evaluate' para 'oab_exams'...")
    evaluate(dataset="oab_exams")

    typer.echo("\n[07/12] Executando 'judgment' para 'oab_bench'...")
    judgment(dataset="oab_bench", judge=judge, model=None, limit=limit)

    typer.echo("\n[08/12] Executando 'curate' para 'oab_bench'...")
    curate(dataset="oab_bench", judge=judge, limit=limit)

    typer.echo("\n[09/12] Executando 'curate' para 'oab_exams'...")
    curate(dataset="oab_exams", judge=judge, limit=limit)

    typer.echo("\n[10/12] Executando 'report' para 'oab_bench'...")
    report(dataset="oab_bench")

    typer.echo("\n[11/12] Executando 'report' para 'oab_exams'...")
    report(dataset="oab_exams")

    typer.echo("\n[12/12] Executando 'build-readme'...")
    build_readme()

    end_time = time.time()
    total_seconds = int(end_time - start_time)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours} hora{'s' if hours > 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minuto{'s' if minutes > 1 else ''}")
    if seconds > 0 or total_seconds == 0:
        parts.append(f"{seconds} segundo{'s' if seconds != 1 else ''}")

    if len(parts) > 1:
        time_str = ", ".join(parts[:-1]) + f" e {parts[-1]}"
    else:
        time_str = parts[0]

    typer.echo(
        f"\n=== Pipeline completo finalizado com sucesso! Tempo de execução: {time_str} ==="
    )
