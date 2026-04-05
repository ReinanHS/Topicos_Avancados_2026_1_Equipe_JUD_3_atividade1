<div align="center">

<img src="https://upload.wikimedia.org/wikipedia/commons/1/1c/Ufs_principal_positiva-nova.png" alt="ufs-logo" width="20%">

<h1>Tópicos Avançados ES e SI</h1>

<h3>Atividade Avaliativa 1 — Curadoria de Datasets e Inferência Básica com LLMs</h3>

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/reinanhs/Topicos_Avancados_2026_1_Equipe_JUD_3_atividade1?machine=standardLinux2gb)

<p align="center">
  <!-- Python version -->
  <img src="https://img.shields.io/badge/python-3.12%2B-blue.svg" alt="Python 3.12+">
  <!-- License -->
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="Licença MIT">
  </a>
  <!-- PDF -->
  <a href="https://reinanhs.github.io/Topicos_Avancados_2026_1_Equipe_JUD_3_atividade1/contribuicao-individual.pdf">
    <img src="https://img.shields.io/badge/Contribui%C3%A7%C3%A3o%20individual-PDF-red.svg?logo=libreofficewriter" alt="PDF">
  </a>
  <!-- Last commit -->
  <a href="https://github.com/reinanhs/Topicos_Avancados_2026_1_Equipe_JUD_3_atividade1/commits/main">
    <img src="https://img.shields.io/github/last-commit/reinanhs/Topicos_Avancados_2026_1_Equipe_JUD_3_atividade1.svg" alt="Último commit">
  </a>
  <!-- Stars -->
  <a href="https://github.com/reinanhs/Topicos_Avancados_2026_1_Equipe_JUD_3_atividade1/stargazers">
    <img src="https://img.shields.io/github/stars/reinanhs/Topicos_Avancados_2026_1_Equipe_JUD_3_atividade1.svg?style=social" alt="Stars">
  </a>
</p>

</div>

## 📚 Sobre

Repositório da **Equipe 3 (Jurídica)** para a primeira atividade avaliativa da disciplina **Tópicos Avançados em Engenharia de Software e Sistemas de Informação I**. O projeto consiste na curadoria de datasets jurídicos e na realização de inferência básica utilizando Modelos de Linguagem (LLMs), com foco em questões do Exame da OAB (Ordem dos Advogados do Brasil).

## Onde está a documentação

A documentação completa não fica concentrada neste `README.md`. Toda a
documentação do projeto está disponível na pasta `docs/`, e a leitura deve
começar por [`docs/intro.md`][docs-intro].

Para facilitar a navegação, também recomendamos acessar a versão web já
compilada da documentação em [documentação publicada][docs-web]. Veja o exemplo da imagem abaixo: 

![Exemplo de documentação publicada](docs/assets/presentation-documentation.gif)

> Se você quiser entender melhor a abordagem Docs-as-Code utilizada neste
repositório, recomendamos a leitura de
[Docs-as-Code: um guia básico para iniciantes][docs-as-code-artigo].

[docs-intro]: docs/intro.md
[docs-web]: https://reinanhs.github.io/Topicos_Avancados_2026_1_Equipe_JUD_3_atividade1/docs
[docs-as-code-artigo]: https://medium.com/@reinanhs/docs-as-code-um-guia-b%C3%A1sico-para-iniciantes-b65b1e63b53a

## ⚖️ Domínio de atuação

A Equipe 3 atua no **Domínio Jurídico**, trabalhando com os seguintes datasets:

| Dataset | Tipo | Quantidade | Fonte |
|---|---|---|---|
| **J1 — OAB Bench** | Questões Abertas | 210 questões | [maritaca-ai/oab-bench](https://huggingface.co/datasets/maritaca-ai/oab-bench/viewer?row=0) |
| **J2 — OAB Exams** | Múltipla Escolha | 2210 questões | [eduagarcia/oab_exams](https://huggingface.co/datasets/eduagarcia/oab_exams) |

Para uma visão geral dos datasets, consulte as documentações abaixo. Elas
apresentam as principais informações sobre os dois datasets do domínio jurídico
utilizados neste repositório:

- [Visão geral dos datasets](https://reinanhs.github.io/Topicos_Avancados_2026_1_Equipe_JUD_3_atividade1/docs/datasets/overview)
- [Visualização dos dados dos datasets](https://reinanhs.github.io/Topicos_Avancados_2026_1_Equipe_JUD_3_atividade1/resultados/datasets)

## 👥 Colaboradores

Este repositório contém as contribuições realizadas pelo aluno **Reinan Gabriel** no contexto da **Atividade Avaliativa 1** da disciplina **Tópicos Avançados em Engenharia de Software e Sistemas de Informação I**, ministrada na Universidade Federal de Sergipe (UFS), semestre 2026.1.

<div align="center">
<table align="center">
  <tr>
    <td align="center">
      <a href="https://github.com/ReinanHS">
        <img src="https://github.com/reinanhs.png" height="64" width="64" alt="Reinan Gabriel"/>
      </a><br/>
      <a href="https://github.com/ReinanHS">Reinan Gabriel</a>
    </td>
  </tr>
</table>
</div>

## 📹 Vídeo demonstrativo

Recomendamos assistir ao vídeo abaixo, que apresenta os resultados coletados por todos os integrantes da equipe, incluindo o aluno Renan Gabriel.

[![Youtube Video](https://gitlab.com/reinanhs/repo-slide-presentation/-/wikis/uploads/c5e58833db92ec50619f8b302ae8f480/baixados.png)](https://youtu.be/lcOxhH8N3Bo)

- 📹 **Assista ao vídeo completo:** [https://youtu.be/lcOxhH8N3Bo](https://youtu.be/lcOxhH8N3Bo)

---

## Ambiente de execução



### Configuração de hardware

Os experimentos de inferência foram executados em uma máquina local com a
configuração de GPU descrita abaixo:

| Componente                | Especificação           |
|---------------------------|-------------------------|
| **GPU**                   | NVIDIA GeForce GTX 1050 |
| **VRAM dedicada**         | 4,0 GB                  |
| **Memória compartilhada** | 8,0 GB                  |
| **Versão do driver**      | 32.0.15.8228            |
| **Data do driver**        | 20/01/2026              |
| **Versão do DirectX**     | 12 (FL 12.1)            |

Como a GPU possui **4 GB de VRAM dedicada**, os modelos selecionados para os
experimentos foram LLMs compactos, com até aproximadamente **3B parâmetros**,
em versões quantizadas compatíveis com a memória disponível.

- [Detalhes da configuração de hardware](https://reinanhs.github.io/Topicos_Avancados_2026_1_Equipe_JUD_3_atividade1/docs/inference/hardware)

### Modelos de linguagem selecionados

Foram escolhidos **três modelos de linguagem** de diferentes organizações para garantir diversidade de arquiteturas e bases de treinamento na comparação. Todos os modelos são executados localmente via [Ollama](https://ollama.com/).

| # | Modelo       | Desenvolvedor | Parâmetros | Quantização | Tamanho (download) | Contexto máximo | Comando Ollama           |
|---|--------------|---------------|------------|-------------|--------------------|-----------------|--------------------------|
| 1 | Llama 3.2 3B | Meta          | 3,21B      | Q4_K_M      | ~2,0 GB            | 128K tokens     | `ollama run llama3.2:3b` |
| 2 | Gemma 2 2B   | Google        | 2,61B      | Q4_0        | ~1,6 GB            | 8K tokens       | `ollama run gemma2:2b`   |
| 3 | Qwen 2.5 3B  | Alibaba Cloud | 3,09B      | Q4_K_M      | ~1,9 GB            | 32K tokens      | `ollama run qwen2.5:3b`  |

- [Documentação sobre os modelos de linguagem selecionados](https://reinanhs.github.io/Topicos_Avancados_2026_1_Equipe_JUD_3_atividade1/docs/inference/models)

---

## Instruções de execução

### Pré-requisitos

Antes de instalar e executar o projeto, verifique se o ambiente possui as ferramentas necessárias. Esta página lista os requisitos obrigatórios e os itens recomendados para uma execução mais estável dos modelos locais.

| Requisito                                     | Versão mínima | Descrição                                            |
|-----------------------------------------------|---------------|------------------------------------------------------|
| [Python](https://www.python.org/downloads/)   | 3.12+         | Linguagem principal utilizada no projeto             |
| [UV](https://docs.astral.sh/uv/#installation) | 0.10+         | Gerenciador de dependências e ambientes Python       |
| [Ollama](https://ollama.com/download)         | 0.19+       | Runtime para execução local dos modelos de linguagem |
| [Git](https://git-scm.com/install)            | 2.x           | Ferramenta de controle de versão                     |

- [Documentação sobre os pré-requisitos](https://reinanhs.github.io/Topicos_Avancados_2026_1_Equipe_JUD_3_atividade1/docs/getting-started/prerequisites)

### Instalação e execução

Consulte as documentações abaixo para preparar o ambiente, instalar as
dependências e baixar os modelos usados nas execuções locais:

- [Instalação e execução](https://reinanhs.github.io/Topicos_Avancados_2026_1_Equipe_JUD_3_atividade1/docs/getting-started/installation)
- [Guia rápido](https://reinanhs.github.io/Topicos_Avancados_2026_1_Equipe_JUD_3_atividade1/docs/getting-started/quick-start)

Se preferir uma visão resumida, siga os passos abaixo para executar o projeto
localmente:

```bash
# (Opcional) Criar e ativar um ambiente virtual
python -m venv .venv

# Ativação no Linux/macOS
source .venv/bin/activate

# Ativação no Windows (PowerShell)
# .venv\Scripts\activate

# Instalar as dependências do projeto
uv sync

# Executar o script principal
uv run python main.py

# Baixar os datasets
uv run python main.py pull oab_bench
uv run python main.py pull oab_exams

# Executar a inferência no dataset oab_bench
uv run python main.py infer oab_bench --model llama3.2:3b
uv run python main.py infer oab_bench --model gemma2:2b
uv run python main.py infer oab_bench --model qwen2.5:3b

# Executar a inferência no dataset oab_exams
uv run python main.py infer oab_exams --model llama3.2:3b
uv run python main.py infer oab_exams --model gemma2:2b
uv run python main.py infer oab_exams --model qwen2.5:3b

# Avaliar os resultados das inferências
uv run python main.py evaluate oab_bench
uv run python main.py evaluate oab_exams

# Julgar as respostas dos modelos
uv run python main.py judgment oab_bench
```

---

## 📄 Licença

Este projeto está licenciado sob a Licença MIT — veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<div align="center">
  <sub>Desenvolvido com dedicação pela Equipe 3 — Domínio Jurídico | UFS — 2026.1</sub>
</div>
