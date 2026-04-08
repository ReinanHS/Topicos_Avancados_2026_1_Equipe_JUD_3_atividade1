---
sidebar_position: 2
---

# ROUGE

## O que é

O **ROUGE** (*Recall-Oriented Understudy for Gisting Evaluation*) é um conjunto
de métricas usado para avaliar textos gerados com base na cobertura do conteúdo
de uma referência.

Diferentemente do BLEU, o ROUGE enfatiza **recall**, ou seja, mede quanto do
conteúdo presente no texto de referência também aparece no texto gerado.

## Variantes utilizadas

| Variante    | O que mede                               |
|-------------|------------------------------------------|
| **ROUGE-1** | Sobreposição de unigramas                |
| **ROUGE-2** | Sobreposição de bigramas                 |
| **ROUGE-L** | Maior subsequência comum entre os textos |

### ROUGE-1

O **ROUGE-1** mede quantas palavras da referência aparecem no texto gerado.

Essa variante é útil para avaliar a cobertura geral do vocabulário.

### ROUGE-2

O **ROUGE-2** mede quantos pares de palavras consecutivas da referência aparecem
no texto gerado.

Essa variante ajuda a avaliar similaridade local de estrutura e formulação.

### ROUGE-L

O **ROUGE-L** mede a maior subsequência comum entre o texto gerado e a
referência.

Essa variante é útil para capturar similaridade estrutural mais ampla entre os
textos.

## Interpretação da escala

O ROUGE varia de **0** a **1**:

- **0** indica ausência de cobertura relevante do conteúdo da referência.
- **1** indica cobertura completa.

## Diferença em relação ao BLEU

| Aspecto            | BLEU                                  | ROUGE                                             |
|--------------------|---------------------------------------|---------------------------------------------------|
| Foco               | Precisão                              | Recall                                            |
| Pergunta principal | O texto gerado aparece na referência? | O conteúdo da referência aparece no texto gerado? |
| Uso comum          | Tradução automática                   | Sumarização e geração de texto                    |

Assim como o BLEU, o ROUGE é baseado em sobreposição de palavras e não captura
similaridade semântica. Para esse tipo de análise, utilize o
[BERTScore](bertscore.md).
