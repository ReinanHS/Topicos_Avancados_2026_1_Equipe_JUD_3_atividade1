import re
from pathlib import Path
from typing import Dict, List, Any
from bs4 import BeautifulSoup


class LegislationChunker:
    """
    Filtra e divide documentos HTML de legislação brasileira em artigos contíguos (chunks).
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

        chunks = []
        current_chunk = []
        current_art = "Preâmbulo"
        law_name = file_path.stem

        # Mapeia nomes amigáveis para as leis comuns do diretório
        friendly_names = {
            "Constituição": "Constituição Federal de 1988",
            "Del5452compilado": "Consolidação das Leis do Trabalho (CLT)",
            "L10406compilada": "Código Civil Brasileiro (Lei 10.406/2002)",
            "L13146": "Estatuto da Pessoa com Deficiência (Lei 13.146/2015)",
            "L13869": "Lei de Abuso de Autoridade (Lei 13.869/2019)",
            "L14133": "Nova Lei de Licitações (Lei 14.133/2021)",
            "L8078compilado": "Código de Defesa do Consumidor (Lei 8.078/1990)",
            "L8429compilada": "Lei de Improbidade Administrativa (Lei 8.429/1992)",
        }
        law_title = friendly_names.get(law_name, law_name)

        for line in lines:
            match = self.art_pattern.match(line)
            if match:
                # Salva o chunk anterior antes de começar um novo artigo
                if current_chunk:
                    chunks.append(
                        {
                            "article": current_art,
                            "text": "\n".join(current_chunk),
                            "law_title": law_title,
                            "file_name": file_path.name,
                        }
                    )
                # Extrai a numeração do artigo formatada
                current_art = match.group(1).strip()
                # Remove espaços internos do termo 'Art. X'
                current_art = re.sub(r"\s+", " ", current_art)
                current_chunk = [line]
            else:
                current_chunk.append(line)

        # Salva o último chunk pendente
        if current_chunk:
            chunks.append(
                {
                    "article": current_art,
                    "text": "\n".join(current_chunk),
                    "law_title": law_title,
                    "file_name": file_path.name,
                }
            )

        return chunks
