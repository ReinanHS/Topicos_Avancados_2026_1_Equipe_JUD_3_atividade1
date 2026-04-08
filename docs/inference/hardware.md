---
sidebar_position: 3
---

# Hardware

## Configuração utilizada

Os experimentos de inferência foram executados em uma máquina local com a
seguinte configuração:

| Componente                | Especificação           |
|---------------------------|-------------------------|
| **GPU**                   | NVIDIA GeForce GTX 1050 |
| **VRAM dedicada**         | 4,0 GB                  |
| **Memória compartilhada** | 8,0 GB                  |
| **Versão do driver**      | 32.0.15.8228            |
| **Data do driver**        | 20/01/2026              |
| **Versão do DirectX**     | 12 (FL 12.1)            |

## Considerações

Os modelos selecionados são compatíveis com os **4 GB de VRAM dedicada**
disponíveis na GPU.

Durante a inferência:

- Apenas um modelo é carregado por vez
- A execução ocorre diretamente na GPU
- Não é necessário offloading para a RAM
- O Ollama gerencia automaticamente o carregamento e o descarregamento dos
  modelos