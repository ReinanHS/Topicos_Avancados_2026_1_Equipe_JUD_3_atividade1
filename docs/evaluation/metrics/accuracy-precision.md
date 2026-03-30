---
sidebar_position: 4
---

# Acurácia, precisão, recall e F1

Estas métricas de classificação são utilizadas na avaliação exata do dataset
`OAB Exams`. Como esse conjunto possui gabarito oficial, é possível comparar
diretamente as respostas geradas pelo modelo com as respostas corretas.

## Acurácia

A **acurácia** é a métrica mais intuitiva. Ela indica quantas questões o modelo
acertou em relação ao total de questões avaliadas.

Neste projeto, o lote contém **122 questões**. Se o modelo `gemma2:2b` acertou
**55** dessas 122 questões, a acurácia é calculada como `55 / 122`, o que
resulta em aproximadamente **0,4508**.

Essa métrica oferece uma visão geral do desempenho do modelo. Em termos
práticos, ela ajuda a responder à seguinte pergunta: de forma global, quantas
questões o modelo acertou? Considerando como referência um mínimo de **50%**,
nenhum dos três modelos avaliados alcançaria esse patamar.

No código, a acurácia é calculada da seguinte forma:

```python
acc_score = self._get_metric("accuracy").compute(
    predictions=predictions, references=references
)
````

Nesse trecho, `predictions` representa os inteiros correspondentes às respostas
geradas pelo modelo, enquanto `references` representa os inteiros associados ao
gabarito oficial.

## Precisão

A **precisão**, neste caso calculada com média **macro**, observa o problema por
outra perspectiva. Ela mede, para cada alternativa, quantas vezes o modelo
esteve correto quando escolheu aquela alternativa.

Por exemplo, suponha que o modelo tenha respondido a alternativa **C** em
**30 questões**. Dessas 30, apenas **12** realmente tinham **C** como gabarito.
Nesse caso, a precisão da classe **C** é `12 / 30 = 0,40`.

Esse cálculo é feito separadamente para cada classe, ou seja, para as
alternativas **A**, **B**, **C** e **D**. Em seguida, é calculada a média
simples entre esses valores. É isso que caracteriza a média **macro**.

No contexto desta atividade, uma precisão baixa em determinada alternativa pode
indicar que o modelo tende a escolher aquela letra com frequência, mesmo quando
ela não corresponde à resposta correta.

O código utilizado é o seguinte:

```python
prec_score = self._get_metric("precision").compute(
    predictions=predictions,
    references=references,
    average="macro",
    zero_division=0,
)
```

O parâmetro `zero_division=0` é importante porque evita problemas quando o
modelo não escolhe alguma alternativa durante toda a avaliação. Nessa situação,
a divisão por zero é tratada como valor `0` para a precisão daquela classe.

## Recall

O **recall**, também calculado com média **macro**, inverte a lógica da
precisão. Em vez de perguntar quantas previsões do modelo estavam corretas,
ele pergunta quantas questões de uma determinada classe foram corretamente
identificadas pelo modelo.

Por exemplo, imagine que **35 questões** tenham a alternativa **B** como
gabarito oficial, mas o modelo só tenha marcado **B** corretamente em
**10 delas**. Nesse caso, o recall da classe **B** é `10 / 35`, o que resulta
em aproximadamente **0,286**.

Esse valor mostra que o modelo deixou de reconhecer várias questões cujo
gabarito correto era **B**. Em um cenário de análise mais detalhada, isso pode
ajudar a identificar fragilidades recorrentes em certos padrões de resposta.

O cálculo no código é feito assim:

```python
rec_score = self._get_metric("recall").compute(
    predictions=predictions,
    references=references,
    average="macro",
    zero_division=0,
)
```

Assim como na precisão, o parâmetro `zero_division=0` evita erros quando há
classes sem previsões válidas para o cálculo.

## F1

O **F1**, também calculado com média **macro**, combina **precisão** e
**recall** em uma única métrica. Ele é útil porque penaliza cenários em que o
modelo apresenta bom desempenho em apenas uma dessas dimensões.

Se a precisão for alta e o recall for baixo, ou o contrário, o valor de F1 não
será alto. Por isso, essa métrica é frequentemente utilizada como uma medida de
equilíbrio entre os dois aspectos.

A fórmula do F1 é:

```text
F1 = 2 × (Precisão × Recall) / (Precisão + Recall)
```

O cálculo é realizado individualmente para cada classe e, ao final, é feita a
média simples entre as classes.

No código, o cálculo aparece da seguinte forma:

```python
f1_score = self._get_metric("f1").compute(
    predictions=predictions, references=references, average="macro"
)
```

Nesta atividade, o F1 é uma métrica particularmente útil porque oferece uma
visão mais equilibrada do desempenho geral do modelo no problema de
classificação multiclasse.
