---
sidebar_position: 1
---

# BLEU

## O que é

O **BLEU** (*Bilingual Evaluation Understudy*) é uma métrica usada para avaliar
textos gerados por modelos de linguagem com base na sobreposição de
**n-gramas** entre o texto gerado e um texto de referência.

A métrica foi criada para avaliação de tradução automática, mas também é usada
em tarefas de geração de texto.

## Como funciona

O cálculo do BLEU considera os seguintes passos:

1. Extrai os n-gramas do texto gerado e do texto de referência.
2. Calcula a precisão de n-gramas, verificando quantos n-gramas do texto
   gerado também aparecem na referência.
3. Aplica uma penalidade para textos muito curtos.
4. Combina os resultados de diferentes ordens de n-gramas, como 1-gramas,
   2-gramas, 3-gramas e 4-gramas.

## Interpretação da escala

O BLEU varia de **0** a **1**:

- **0** indica ausência de sobreposição relevante de n-gramas.
- **1** indica correspondência perfeita entre o texto gerado e a referência.

Na prática, textos longos ou com maior variação de escrita costumam apresentar
valores mais baixos, mesmo quando o conteúdo está correto.

## Limitações

O BLEU possui as seguintes limitações:

- Considera apenas correspondência exata de palavras
- Não captura sinônimos nem similaridade semântica
- Pode penalizar respostas corretas que usam redação diferente da referência
- Tende a funcionar melhor em textos curtos e mais objetivos do que em textos
  longos e argumentativos
