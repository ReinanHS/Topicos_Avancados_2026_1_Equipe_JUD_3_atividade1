---
sidebar_position: 1
---

# Pré-requisitos

Antes de instalar e executar o projeto, verifique se o ambiente possui as ferramentas necessárias. Esta página lista os requisitos obrigatórios e os itens recomendados para uma execução mais estável dos modelos locais.

## Requisitos obrigatórios

| Requisito                                     | Versão mínima | Descrição                                            |
|-----------------------------------------------|---------------|------------------------------------------------------|
| [Python](https://www.python.org/downloads/)   | 3.12+         | Linguagem principal utilizada no projeto             |
| [UV](https://docs.astral.sh/uv/#installation) | Atual         | Gerenciador de dependências e ambientes Python       |
| [Ollama](https://ollama.com/download)         | Atual         | Runtime para execução local dos modelos de linguagem |
| [Git](https://git-scm.com/install)            | 2.x           | Ferramenta de controle de versão                     |

## Requisitos recomendados

| Requisito  | Descrição                                                                       |
|------------|---------------------------------------------------------------------------------|
| GPU NVIDIA | Pelo menos 4 GB de VRAM para executar modelos quantizados com melhor desempenho |
| CUDA       | Drivers compatíveis com o Ollama para uso da GPU NVIDIA                         |

## Como verificar a instalação

Execute os comandos abaixo para confirmar se as ferramentas estão disponíveis no
ambiente:

```bash
python --version
uv --version
ollama --version
git --version
````

:::info 
Caso não possua GPU dedicada, é possível executar os modelos em CPU, porém o tempo de inferência será significativamente maior. 
:::