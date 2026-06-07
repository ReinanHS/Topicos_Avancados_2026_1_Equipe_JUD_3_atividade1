import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Any
from bs4 import BeautifulSoup


def strip_accents(text: str) -> str:
    """Remove acentuação de uma string."""
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


class LegislationChunker:
    """
    Filtra e divide documentos HTML de legislação brasileira em artigos contíguos (chunks).
    Extrai hierarquias estruturais (Parte, Livro, Título, Capítulo, Seção, Subseção)
    e metadados avançados.
    """

    def __init__(self):
        # Padrão para identificar início de artigo no começo de uma linha
        # Exemplos: "Art. 1º", "Art. 10", "art. 1-A", "Artigo 15"
        self.art_pattern = re.compile(
            r"^(art\.\s*\d+|art\s+\d+|artigo\s+\d+)", re.IGNORECASE
        )

    def clean_html_to_lines(self, html_content: str) -> List[str]:
        """
        Remove elementos HTML desnecessários e retorna as linhas do texto normalizado.
        Substitui as quebras de linha existentes por espaços para evitar a quebra
        de termos como 'Art.\n2º' antes de processar os blocos de parágrafos.
        """
        # Normaliza quebras de linha brutas em espaços para evitar corte de palavras
        html_single_line = html_content.replace("\r", " ").replace("\n", " ")

        soup = BeautifulSoup(html_single_line, "html.parser")

        # Deleta tags de metadados, scripts e estilo
        for tag_to_remove in ["script", "style", "head", "title", "meta"]:
            for element in soup.find_all(tag_to_remove):
                element.decompose()

        # Insere quebras de linha após tags de bloco para delimitar os parágrafos corretos
        block_tags = ["p", "div", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "li", "br"]
        for tag in block_tags:
            for element in soup.find_all(tag):
                element.insert_after("\n")

        raw_text = soup.get_text()

        # Limpa e filtra as linhas resultantes
        lines = []
        for line in raw_text.splitlines():
            line_clean = line.strip()
            # Normaliza múltiplos espaços em branco
            line_clean = re.sub(r"\s+", " ", line_clean)
            if line_clean:
                lines.append(line_clean)

        return lines

    def _get_heading_level_and_text(
        self, normalized_line: str, raw_line: str
    ) -> tuple[str | None, str | None]:
        """Identifica se uma linha é um cabeçalho estrutural e qual o seu nível."""
        # Se for muito longo, provavelmente é texto corrido
        if len(raw_line) > 150:
            return None, None

        patterns = {
            "subsecao": r"^SUBSECAO\s+(?:[IVXLCDM\d]+|UNICA)\b",
            "secao": r"^SECAO\s+(?:[IVXLCDM\d]+|UNICA)\b",
            "capitulo": r"^CAPITULO\s+(?:[IVXLCDM\d\s]+|UNICO)\b",
            "titulo": r"^TITULO\s+(?:[IVXLCDM\d]+|UNICO)\b",
            "livro": r"^LIVRO\s+(?:[IVXLCDM\d]+)\b",
            "parte": r"^PARTE\s+(?:GERAL|ESPECIAL|[IVXLCDM\d]+)\b",
        }

        for level, pat in patterns.items():
            if re.match(pat, normalized_line):
                return level, raw_line
        return None, None

    def chunk_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Lê o arquivo HTML, limpa o conteúdo e divide em artigos.
        Retorna uma lista de dicionários contendo o artigo, texto e metadados.
        """
        try:
            with open(file_path, "r", encoding="latin1") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

        lines = self.clean_html_to_lines(content)

        # Normalização do nome da lei
        stem_norm = strip_accents(file_path.stem).lower()

        friendly_names = {
            "constituicao": "Constituição Federal de 1988",
            "del2848compilado": "Código Penal (Decreto-Lei 2.848/1940)",
            "del5452compilado": "Consolidação das Leis do Trabalho (CLT)",
            "l10406compilada": "Código Civil (Lei 10.406/2002)",
            "l11101": "Lei de Recuperação Judicial e Falências (Lei 11.101/2005)",
            "l11284": "Lei de Gestão de Florestas Públicas (Lei 11.284/2006)",
            "l13146": "Estatuto da Pessoa com Deficiência (Lei 13.146/2015)",
            "l13869": "Lei de Abuso de Autoridade (Lei 13.869/2019)",
            "l14133": "Nova Lei de Licitações (Lei 14.133/2021)",
            "l5474": "Lei das Duplicatas (Lei 5.474/1968)",
            "l6404consol": "Lei das Sociedades por Ações (Lei 6.404/1976)",
            "l8069compiladoa": "Estatuto da Criança e do Adolescente (ECA)",
            "l8078compilado": "Código de Defesa do Consumidor (CDC)",
            "l8429compilada": "Lei de Improbidade Administrativa (Lei 8.429/1992)",
            "l9279": "Lei da Propriedade Industrial (Lei 9.279/1996)",
        }
        law_title = friendly_names.get(stem_norm, file_path.stem)

        legal_areas = {
            "constituicao": "Direito Constitucional",
            "del2848compilado": "Direito Penal",
            "del5452compilado": "Direito do Trabalho",
            "l10406compilada": "Direito Civil",
            "l11101": "Direito Empresarial",
            "l11284": "Direito Ambiental",
            "l13146": "Direito Civil",
            "l13869": "Direito Penal",
            "l14133": "Direito Administrativo",
            "l5474": "Direito Empresarial",
            "l6404consol": "Direito Empresarial",
            "l8069compiladoa": "Direito da Criança e do Adolescente",
            "l8078compilado": "Código de Defesa do Consumidor (CDC)",
            "l8429compilada": "Lei de Improbidade Administrativa (Lei 8.429/1992)",
            "l9279": "Direito Empresarial",
        }
        legal_area = legal_areas.get(stem_norm, "Direito")

        # Lista de palavras-chave do domínio jurídico brasileiro
        legal_keywords_pool = [
            "estado de perigo",
            "coacao",
            "dolo",
            "erro",
            "lesao",
            "fraude contra credores",
            "simulacao",
            "nulidade",
            "anulabilidade",
            "anulacao",
            "contrato",
            "responsabilidade civil",
            "indenizacao",
            "prescricao",
            "decadencia",
            "posse",
            "propriedade",
            "obrigacao",
            "solidariedade",
            "pagamento",
            "mora",
            "perdas e danos",
            "juros",
            "clausula penal",
            "arras",
            "eviccao",
            "vicio redibitorio",
            "alimentos",
            "divorcio",
            "casamento",
            "guarda",
            "adocao",
            "sucessao",
            "heranca",
            "testamento",
            "inventario",
            "partilha",
            "usucapiao",
            "hipoteca",
            "penhor",
            "alienacao fiduciaria",
            "abuso de autoridade",
            "improbidade administrativa",
            "licitacao",
            "consumidor",
            "trabalho",
            "crime",
            "pena",
            "reincidencia",
            "prescricao penal",
            "liberdade",
            "prisao",
            "flagrante",
            "busca e apreensao",
            "processo",
            "contestacao",
            "recurso",
            "apelacao",
            "agravo",
            "monitoria",
            "execucao",
            "cumprimento de sentenca",
            "tutela",
            "liminar",
            "audiencia",
            "pericia",
        ]

        current_headings = {
            "parte": "",
            "livro": "",
            "titulo": "",
            "capitulo": "",
            "secao": "",
            "subsecao": "",
        }

        chunks = []
        current_chunk = []
        current_art = "Preâmbulo"

        def save_current_chunk():
            nonlocal current_chunk, current_art
            if not current_chunk or current_art is None:
                return

            # Constrói o heading_path ativo
            heading_levels = []
            for lvl in ["parte", "livro", "titulo", "capitulo", "secao", "subsecao"]:
                if current_headings[lvl]:
                    heading_levels.append(current_headings[lvl])
            heading_path = " > ".join(heading_levels)

            raw_text = "\n".join(current_chunk)

            # Prepara a contextualização prepended no texto
            prefix_parts = [law_title]
            if heading_path:
                prefix_parts.append(heading_path)
            prefix = f"[{' - '.join(prefix_parts)}] "

            # Texto indexado inclui a hierarquia e o título da lei
            contextualized_text = prefix + raw_text

            # Normalização de número do artigo
            # Exemplo: "Art. 156" -> "156"
            art_number_match = re.search(r"\d+", current_art)
            art_number = art_number_match.group(0) if art_number_match else ""

            # Extração de palavras-chave a partir do texto
            text_norm = strip_accents(raw_text).lower()
            keywords = []
            for kw in legal_keywords_pool:
                if kw in text_norm:
                    keywords.append(kw)

            chunks.append(
                {
                    "article": current_art,
                    "article_number": art_number,
                    "text": contextualized_text,
                    "raw_text": raw_text,
                    "law_title": law_title,
                    "file_name": file_path.name,
                    "legal_area": legal_area,
                    "keywords": keywords,
                    "heading_path": heading_path,
                }
            )
            current_chunk = []

        for line in lines:
            line_clean = line.strip()
            line_norm = strip_accents(line_clean).upper()

            # 1. Verifica se a linha é um cabeçalho estrutural
            level, heading_text = self._get_heading_level_and_text(
                line_norm, line_clean
            )
            if level:
                # Salva o artigo anterior se existir
                save_current_chunk()

                # Atualiza a estrutura hierárquica e limpa os subníveis
                current_headings[level] = heading_text
                levels_to_clear = []
                if level == "parte":
                    levels_to_clear = [
                        "livro",
                        "titulo",
                        "capitulo",
                        "secao",
                        "subsecao",
                    ]
                elif level == "livro":
                    levels_to_clear = ["titulo", "capitulo", "secao", "subsecao"]
                elif level == "titulo":
                    levels_to_clear = ["capitulo", "secao", "subsecao"]
                elif level == "capitulo":
                    levels_to_clear = ["secao", "subsecao"]
                elif level == "secao":
                    levels_to_clear = ["subsecao"]

                for l in levels_to_clear:
                    current_headings[l] = ""

                # Entra na zona de transição e limpa buffer
                current_art = None
                current_chunk = []
                continue

            # 2. Verifica se a linha indica o início de um novo artigo
            art_match = self.art_pattern.match(line_clean)
            if art_match:
                # Salva o chunk do artigo anterior se existir
                save_current_chunk()

                # Seta o novo artigo
                current_art = art_match.group(1).strip()
                current_art = re.sub(r"\s+", " ", current_art)
                current_chunk = [line_clean]
            else:
                # Se estivermos processando um artigo ativo (ou pré-âmbulo), acumula
                if current_art is not None:
                    current_chunk.append(line_clean)

        # Salva o último artigo pendente
        save_current_chunk()

        return chunks
