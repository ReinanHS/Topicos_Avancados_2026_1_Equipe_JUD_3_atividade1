---
sidebar_position: 3
---

# BERTScore

O **BERTScore** é uma métrica de similaridade semântica baseada em embeddings
contextualizados. Em vez de comparar apenas palavras iguais, ela compara o
significado dos textos por meio da similaridade cosseno entre os vetores gerados
por um modelo Transformer. Por isso, ela é útil quando duas respostas dizem
praticamente a mesma coisa com palavras diferentes.

## Como funciona

O cálculo é feito em três partes:

- **Precisão**: verifica se os tokens gerados pela predição encontram
  correspondências semânticas no texto de referência.
- **Recall**: verifica se os conceitos importantes da referência aparecem na
  predição.
- **F1**: combina precisão e recall em um único valor.

Neste projeto, o valor principal reportado é o **F1 médio**, pois ele resume
melhor o equilíbrio entre cobertura e aderência semântica. O `BERTScore`
retorna listas de `precision`, `recall` e `f1`, uma por par de textos
comparados.

## Por que usar nesta atividade

No `OAB Bench`, a avaliação é cruzada entre respostas de modelos diferentes.
Como essas respostas podem usar vocabulário distinto para expressar a mesma
ideia jurídica, métricas lexicais como BLEU e ROUGE nem sempre capturam bem essa
proximidade. O `BERTScore` reduz esse problema porque considera similaridade
semântica, e não apenas sobreposição literal de palavras.

## Como calcular no código

```python
bert_score_raw = self._get_metric("bertscore").compute(
    predictions=predictions,
    references=references,
    lang="pt",
)

bert_f1_mean = (
    sum(bert_score_raw["f1"]) / len(bert_score_raw["f1"])
    if bert_score_raw["f1"]
    else 0.0
)
````

Nesse exemplo, `predictions` contém as respostas geradas e `references` contém
as respostas usadas como comparação.

## Como customizar o modelo de embeddings

Para usar o `BERTScore`, é necessário informar `lang` **ou** `model_type`. Se
você passa `lang="pt"`, a biblioteca escolhe automaticamente um modelo sugerido
para esse idioma. Se quiser sobrescrever esse comportamento, use
`model_type` com o nome de um checkpoint do Hugging Face.

Importante: na prática, você **não passa os embeddings prontos**. Você informa
qual modelo deve gerar os embeddings, e a própria métrica faz o restante.

Exemplo com modelo explícito:

```python
bert_score_raw = self._get_metric("bertscore").compute(
    predictions=predictions,
    references=references,
    model_type="google-bert/bert-base-multilingual-cased",
)
```

O modelo `google-bert/bert-base-multilingual-cased` é um checkpoint multilíngue
treinado em 104 idiomas, incluindo português, e pode ser usado quando você
quiser controlar explicitamente qual modelo gera os embeddings. ([Hugging Face][2])

Se necessário, você também pode ajustar `num_layers` para escolher a camada
usada na representação, já que o valor padrão depende do `model_type`
selecionado.

Exemplo com camada explícita:

```python
bert_score_raw = self._get_metric("bertscore").compute(
    predictions=predictions,
    references=references,
    model_type="google-bert/bert-base-multilingual-cased",
    num_layers=8,
)
```

## Ajuste de baseline

A métrica também aceita `rescale_with_baseline=True` e `baseline_path` para usar
um baseline customizado. Nesse caso, a documentação do `evaluate` informa que
`lang` deve ser especificado quando o reescalonamento com baseline estiver
ativado.

Exemplo:

```python
bert_score_raw = self._get_metric("bertscore").compute(
    predictions=predictions,
    references=references,
    lang="pt",
    rescale_with_baseline=True,
    baseline_path="data/baselines/bertscore_pt.tsv",
)
```
