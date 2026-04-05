import typer

app = typer.Typer(no_args_is_help=True)


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
    Se --model não for informado, executa para todos os modelos disponíveis.
    """
    from src.datasets.loader_factory import DatasetLoaderFactory
    from src.execution.executor_factory import ExecutionManagerFactory
    from src.llm.ollama_client import OllamaClient
    from src.storage.local_storage import LocalStorage

    if dataset not in DatasetLoaderFactory.available_datasets():
        typer.echo(
            f"Erro: Dataset '{dataset}' não reconhecido. "
            f"Use: {', '.join(DatasetLoaderFactory.available_datasets())}.",
            err=True,
        )
        raise typer.Exit(code=1)

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

    for current_model in models_to_run:
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
    """
    Avalia as respostas geradas comparando-as de forma cruzada (um modelo como referência para o outro) ou exata.
    O sistema detecta automaticamente quais modelos já possuem resultados salvos para este dataset.
    """
    from src.datasets.loader_factory import DatasetLoaderFactory
    from src.evaluation.cross_model_evaluator import CrossModelEvaluator
    from src.evaluation.exact_match_evaluator import ExactMatchEvaluator
    from src.storage.local_storage import LocalStorage

    if dataset not in DatasetLoaderFactory.available_datasets():
        typer.echo(
            f"Erro: Dataset '{dataset}' não reconhecido. "
            f"Use: {', '.join(DatasetLoaderFactory.available_datasets())}.",
            err=True,
        )
        raise typer.Exit(code=1)

    storage = LocalStorage()

    typer.echo(f"Buscando modelos disponíveis para o dataset {dataset}...")
    models = storage.list_available_models(dataset)

    if dataset == "oab_bench":
        if len(models) < 2:
            typer.echo(
                f"Foram encontrados resultados para apenas {len(models)} modelo(s): {models}."
            )
            typer.echo(
                "Erro: Para a avaliação cruzada, é necessário primeiro fazer a execução "
                "para ter os resultados salvos (no mínimo 2 modelos).",
                err=True,
            )
            typer.echo(
                f"Sugestão: Execute 'uv run python main.py infer {dataset} --model <nome_do_modelo>' "
                "para novos modelos."
            )
            raise typer.Exit(code=1)

        typer.echo(f"Modelos encontrados ({len(models)}): {', '.join(models)}")
        typer.echo("Iniciando a avaliação cruzada (Pairwise Metrics)...")

        try:
            evaluator = CrossModelEvaluator(storage)
            cross_scores = evaluator.evaluate(dataset, models)
            typer.echo("\n--- Resultados da Avaliação Cruzada ---")
            for pair, scores in cross_scores.items():
                typer.echo(f"\n[{pair}]")
                for section, metrics in scores.items():
                    typer.echo(f"  {section.upper()}:")
                    for metric, value in metrics.items():
                        typer.echo(f"    {metric.upper()}: {value:.4f}")

            for model in models:
                model_metrics = {}
                for pair, scores in cross_scores.items():
                    if model in pair:
                        model_metrics[pair] = scores

                filename = model.replace(":", "-")
                output_path = storage.save_data(
                    [model_metrics],
                    filename,
                    fmt="json",
                    sub_dir=f"results/{dataset}/model_metric",
                )
                typer.echo(f"Métricas de {model} salvas em: {output_path}")

        except Exception as e:
            typer.echo(f"Erro durante a avaliação: {e}", err=True)
            raise typer.Exit(code=1)

    elif dataset == "oab_exams":
        if len(models) < 1:
            typer.echo(
                "Erro: Nenhum modelo encontrado para 'oab_exams'. "
                "Execute o comando 'infer' primeiro para gerar os resultados.",
                err=True,
            )
            raise typer.Exit(code=1)

        typer.echo(f"Modelos encontrados ({len(models)}): {', '.join(models)}")
        typer.echo("Iniciando a avaliação exata (Acurácia, Precisão, Recall, F1)...")

        try:
            evaluator = ExactMatchEvaluator(storage)
            model_scores = evaluator.evaluate(dataset, models)
            typer.echo("\n--- Resultados da Avaliação ---")
            for mod, scores in model_scores.items():
                typer.echo(f"\n[{mod}]")
                for metric, score in scores.items():
                    typer.echo(f"  {metric.upper()}: {score:.4f}")

            for mod, scores in model_scores.items():
                filename = mod.replace(":", "-")
                output_path = storage.save_data(
                    [scores],
                    filename,
                    fmt="json",
                    sub_dir=f"results/{dataset}/model_metric",
                )
                typer.echo(f"Métricas de {mod} salvas em: {output_path}")

        except Exception as e:
            typer.echo(f"Erro durante a avaliação: {e}", err=True)
            raise typer.Exit(code=1)


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

    if not models:
        typer.echo(
            "Erro: Nenhum modelo encontrado com respostas salvas. "
            "Execute o comando 'infer' primeiro para gerar os resultados.",
            err=True,
        )
        raise typer.Exit(code=1)

    if model:
        if model not in models:
            typer.echo(
                f"Erro: Respostas para o modelo '{model}' não foram encontradas.",
                err=True,
            )
            raise typer.Exit(code=1)
        models_to_run = [model]
    else:
        models_to_run = models

    judge_model = judge if judge else DEFAULT_JUDGE_MODEL
    judge_manager = JudgeManager(storage, judge_model=judge_model)

    typer.echo(
        f"Modelos selecionados ({len(models_to_run)}): {', '.join(models_to_run)}"
    )
    typer.echo(f"Modelo juiz: {judge_model}")
    try:
        q_map, ref_map = judge_manager.prepare_dataset_context(dataset)
        all_models_judgments = []

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
                    all_models_judgments.extend(judgments)

        output_path = judge_manager.save_judgments(dataset, all_models_judgments)
        typer.echo(f"\nJulgamentos salvos com sucesso em: {output_path}")

    except Exception as e:
        typer.echo(f"\nErro durante o julgamento: {e}", err=True)
        raise typer.Exit(code=1)
