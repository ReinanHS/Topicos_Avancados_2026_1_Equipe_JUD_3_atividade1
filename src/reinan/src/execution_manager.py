from typing import List, Dict, Any
from pathlib import Path
import jinja2
import json

class ExecutionManager:
    """
    Gerenciador responsável por orquestrar o processo de inferência.
    """
    def __init__(self, dataset_manager, storage_manager, ollama_manager):
        self.dataset_manager = dataset_manager
        self.storage_manager = storage_manager
        self.ollama_manager = ollama_manager

    def get_questions(self, dataset: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        Carrega as questões do dataset especificado e aplica o limite caso exista.
        """
        if dataset == "oab_bench":
            questions = self.dataset_manager.load_oab_bench()
        elif dataset == "oab_exams":
            questions = self.dataset_manager.load_oab_exams()
        else:
            raise ValueError(f"Dataset desconhecido: {dataset}")

        if limit is not None and limit > 0:
            questions = questions[:limit]
            
        return questions

    def _render_prompt(self, dataset: str, template_name: str, context: dict) -> str:
        """
        Função auxiliar para ler o arquivo .minijinja do disco e renderizá-lo com Jinja2.
        """
        
        prompts_dir = Path(__file__).parent.parent / "prompts"
        template_path = prompts_dir / dataset / template_name
        
        if not template_path.exists():
            return ""
            
        with open(template_path, "r", encoding="utf-8") as f:
            template_str = f.read()
            
        template = jinja2.Template(template_str)
        return template.render(**context)

    def process_question(self, q: Dict[str, Any], model: str, dataset: str) -> Dict[str, Any]:
        """
        Recebe uma questão crua, carrega seus templates locais minijinja, formata o prompt usando Jinja2 
        e extrai a resposta do LLM.
        """

        user_prompt = self._render_prompt(dataset, "user_template.minijinja", q)
        system_prompt = self._render_prompt(dataset, "system_template.minijinja", q)
        
        if not user_prompt:
            user_prompt = q.get("statement", q.get("question", ""))
            if "choices" in q:
                choices_text = [f"{label}) {text}" for label, text in zip(q['choices']['label'], q['choices']['text'])]
                user_prompt += "\n" + "\n".join(choices_text)
                
        if not system_prompt:
            system_prompt = q.get("system", "Você é um assistente prestativo especialista em direito brasileiro.")
        
        try:
            response = self.ollama_manager.generate_response(model, system_prompt, user_prompt)
        except Exception as e:
            response = f"ERRO: {e}"
            
        q_result = q.copy()
        q_result['ollama_response'] = response
        q_result['model_used'] = model

        if dataset == "oab_exams":
            resp_str_clean = response.replace("```json", "").replace("```", "").strip()
            resp_json = json.loads(resp_str_clean)

            q_result['objective_answer'] = resp_json.get("resposta_objetiva", "")
        
        return q_result

    def classify_difficulty(self, q: Dict[str, Any], model: str, dataset: str) -> Dict[str, Any]:
        """
        Classifica o nível de dificuldade da questão usando o template de curador.
        """
        prompts_dir = Path(__file__).parent.parent / "prompts"
        template_path = prompts_dir / "curador" / "difficulty-level" / "user_template.minijinja"
        
        context = q.copy()
        
        if dataset == "oab_exams":
            statement = q.get("question", "")
            if "choices" in q:
                choices_text = [f"{label}) {text}" for label, text in zip(q['choices']['label'], q['choices']['text'])]
                statement += "\n\nAlgumas alternativas:\n" + "\n".join(choices_text)
            context["statement"] = statement
            context["category"] = q.get("area", "Sem Área")
            context["question_id"] = q.get("id", "")
        else:
            context["statement"] = q.get("statement", q.get("question", ""))
            context["category"] = q.get("category", q.get("area", ""))
            context["question_id"] = q.get("question_id", q.get("id", ""))
            
        if not template_path.exists():
            return {**q, "error": f"Template não encontrado em {template_path}"}
            
        with open(template_path, "r", encoding="utf-8") as f:
            template_str = f.read()
            
        template = jinja2.Template(template_str)
        user_prompt = template.render(**context)
        
        system_prompt = "Você é um curador jurídico especializado em questões do Exame da OAB."
        
        try:
            response = self.ollama_manager.generate_response(model, system_prompt, user_prompt)
        except Exception as e:
            response = f"ERRO: {e}"
            
        q_result = q.copy()
        q_result['ollama_response'] = response
        q_result['model_used'] = model
        q_result['task'] = "difficulty-level"

        try:
            resp_str_clean = response.replace("```json", "").replace("```", "").strip()
            resp_json = json.loads(resp_str_clean)
            q_result['dificuldade'] = resp_json.get("dificuldade")
        except Exception:
            pass
            
        return q_result

    def define_basic_legislation(self, q: Dict[str, Any], model: str, dataset: str) -> Dict[str, Any]:
        """
        Identifica a legislação base que fundamenta a questão usando o template de curador.
        """
        prompts_dir = Path(__file__).parent.parent / "prompts"
        template_path = prompts_dir / "curador" / "basic-legislation" / "user_template.minijinja"
        
        context = q.copy()
        
        if dataset == "oab_exams":
            statement = q.get("question", "")
            if "choices" in q:
                choices_text = [f"{label}) {text}" for label, text in zip(q['choices']['label'], q['choices']['text'])]
                statement += "\n\nAlgumas alternativas:\n" + "\n".join(choices_text)
            context["statement"] = statement
            context["category"] = q.get("area", "Sem Área")
            context["question_id"] = q.get("id", "")
        else:
            context["statement"] = q.get("statement", q.get("question", ""))
            context["category"] = q.get("category", q.get("area", ""))
            context["question_id"] = q.get("question_id", q.get("id", ""))
            
        if not template_path.exists():
            return {**q, "error": f"Template não encontrado em {template_path}"}
            
        with open(template_path, "r", encoding="utf-8") as f:
            template_str = f.read()
            
        template = jinja2.Template(template_str)
        user_prompt = template.render(**context)
        
        system_prompt = "Você é um curador jurídico especializado em questões do Exame da OAB."
        
        try:
            response = self.ollama_manager.generate_response(model, system_prompt, user_prompt)
        except Exception as e:
            response = f"ERRO: {e}"
            
        q_result = q.copy()
        q_result['ollama_response'] = response
        q_result['model_used'] = model
        q_result['task'] = "basic-legislation"

        try:
            resp_str_clean = response.replace("```json", "").replace("```", "").strip()
            resp_json = json.loads(resp_str_clean)
            q_result['legislacao_base'] = resp_json.get("legislacao_base")
            q_result['legislacao_secundaria'] = resp_json.get("legislacao_secundaria")
        except Exception:
            pass
            
        return q_result

    def process_full_question(self, q: Dict[str, Any], model: str, dataset: str) -> Dict[str, Any]:
        """
        Executa sequencialmente a inferência da questão, a classificação de dificuldade e a identificação da legislação base.
        """

        q_result = self.process_question(q, model, dataset)
        difficulty_result = self.classify_difficulty(q, model, dataset)
        legislation_result = self.define_basic_legislation(q, model, dataset)
        
        if "error" in difficulty_result and difficulty_result["error"]:
            q_result['dificuldade_error'] = difficulty_result['error']
            
        q_result['dificuldade'] = difficulty_result.get('dificuldade')

        if "error" in legislation_result and legislation_result["error"]:
            q_result['legislacao_error'] = legislation_result['error']
            
        q_result['legislacao_base'] = legislation_result.get('legislacao_base')
        q_result['legislacao_secundaria'] = legislation_result.get('legislacao_secundaria')
        
        return q_result

    def save_results(self, results: List[Dict[str, Any]], dataset: str, model: str) -> Path:
        """
        Salva os resultados consolidados na subpasta definida para o cache.
        """
        filename = f"{dataset}_{model.replace(':', '-')}_results"
        output_path = self.storage_manager.save_data(results, filename, fmt="json", sub_dir="results")
        return output_path
