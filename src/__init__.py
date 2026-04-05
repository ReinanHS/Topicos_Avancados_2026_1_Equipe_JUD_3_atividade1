"""
Pacote principal do projeto reinan-jud.

Re-exporta as classes públicas dos subpacotes para conveniência.
"""

from src.cli.app import app
from src.datasets.loader_factory import DatasetLoaderFactory
from src.datasets.oab_bench_loader import OABBenchLoader
from src.datasets.oab_exams_loader import OABExamsLoader
from src.evaluation.cross_model_evaluator import CrossModelEvaluator
from src.evaluation.exact_match_evaluator import ExactMatchEvaluator
from src.execution.executor_factory import ExecutionManagerFactory
from src.llm.ollama_client import OllamaClient
from src.prompts.renderer import PromptRenderer
from src.storage.local_storage import LocalStorage

__all__ = [
    "app",
    "DatasetLoaderFactory",
    "OABBenchLoader",
    "OABExamsLoader",
    "CrossModelEvaluator",
    "ExactMatchEvaluator",
    "ExecutionManagerFactory",
    "OllamaClient",
    "PromptRenderer",
    "LocalStorage",
]
