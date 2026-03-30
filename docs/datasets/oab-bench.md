---
sidebar_position: 2
---

# OAB Bench

O **OAB Bench** é o dataset utilizado no projeto para trabalhar com questões
dissertativas do Exame da Ordem dos Advogados do Brasil. Ele reúne problemas
jurídicos abertos e materiais de apoio usados no processo de avaliação das
respostas.

## Origem

O dataset `maritaca-ai/oab-bench` foi disponibilizado pela **Maritaca AI** como
parte de um benchmark voltado à avaliação de modelos de linguagem em tarefas de
escrita jurídica relacionadas à segunda fase do exame da OAB.

O objetivo do benchmark é avaliar a capacidade dos modelos de responder
questões discursivas e produzir textos jurídicos com fundamentação adequada,
aproximando o processo de avaliação do contexto real do exame.

Para uma visualização mais detalhada do dataset no projeto, acesse a página
abaixo:

- [Visualização detalhada](/resultados/datasets)

## Estrutura dos campos

A tabela abaixo resume os principais campos usados nas questões do dataset:

| Campo         | Tipo       | Descrição                                               |
|---------------|------------|---------------------------------------------------------|
| `question_id` | `string`   | Identificador único da questão                          |
| `category`    | `string`   | Categoria que agrupa edição do exame e área jurídica    |
| `statement`   | `string`   | Enunciado completo da questão discursiva                |
| `turns`       | `string[]` | Itens ou subquestões que devem ser respondidos          |
| `values`      | `number[]` | Pontuação atribuída a cada item da questão              |
| `system`      | `string`   | Instrução de sistema usada para contextualizar o modelo |

## Subsets

O dataset organiza seu conteúdo em subsets com papéis diferentes no benchmark.
Os principais são:

- `questions`: contém os enunciados das questões, com os campos usados na
  inferência
- `guidelines`: contém as orientações e critérios de correção utilizados na
  avaliação das respostas

Essa separação é importante porque o projeto pode usar uma parte dos dados para
gerar respostas e outra parte como apoio ao processo de avaliação.

## Como o dataset foi usado no projeto

No contexto desta atividade, o OAB Bench foi utilizado principalmente na etapa
de inferência sobre questões abertas. Como esse conjunto trabalha com respostas
discursivas, ele foi útil para comparar a qualidade das saídas produzidas pelos
modelos em termos de argumentação, fundamentação jurídica e aderência ao
problema apresentado.

## Exemplo

O exemplo abaixo mostra uma questão do dataset com seus campos principais:

```json
{
  "question_id": "44_direito_administrativo_questao_1",
  "category": "44_direito_administrativo",
  "statement": "Em janeiro de 2025, a sociedade empresária ABC, após a observância de todas as formalidades legais, celebrou contrato administrativo com a União, visando à reforma de um determinado edifício público.\nNo curso da avença, a Administração Pública Federal alterou, unilateralmente, o pacto, em razão de modificações no projeto, para uma melhor adequação técnica a seus objetivos, ensejando a redução dos custos da obra. Assim sendo, houve uma supressão de 20% (vinte por cento) do valor inicial atualizado do contrato, sem transfiguração do objeto da contratação.\nNesse contexto, os sócios da sociedade empresária, surpresos com o ocorrido, buscaram sua orientação como advogado(a), em especial, porque a contratada já havia adquirido os materiais que seriam empregados na obra, colocando-os no local dos trabalhos.\nDiante dessa situação hipotética, na qualidade de advogado(a) da sociedade empresária e à luz das disposições da Lei nº 14.133/2021, responda aos itens a seguir.\nObs .: o(a) examinando(a) deve fundamentar suas respostas. A mera citação do dispositivo legal não confere pontuação.",
  "turns": [
    "A) A União, ao alterar unilateralmente o contrato administrativo, com a supressão de 20% (vinte por cento) do seu valor inicial atualizado, atuou de forma regular? Justifique. (Valor: 0,65)",
    "B) A União é obrigada a pagar à sociedade empresária ABC os materiais já adquiridos e colocados no local dos trabalhos? Justifique. (Valor: 0,60)"
  ],
  "values": [
    0.65,
    0.6
  ],
  "system": "Você é um bacharel em direito que está realizando a segunda fase da prova da Ordem dos Advogados do Brasil (OAB), organizada pela FGV. Sua tarefa é responder às questões discursivas e elaborar uma peça processual, demonstrando seu conhecimento jurídico, capacidade de raciocínio e habilidade de aplicar a legislação e jurisprudência pertinentes ao caso apresentado.\n\n# ATENÇÃO\n\nNa elaboração dos textos da peça prático-profissional e das respostas às questões discursivas, você deverá incluir todos os dados que se façam necessários, sem, contudo, produzir qualquer identificação ou informações além daquelas fornecidas e permitidas nos enunciados contidos no caderno de prova. A omissão de dados que forem legalmente exigidos ou necessários para a correta solução do problema proposto acarretará em descontos na pontuação atribuída a você nesta fase. Você deve estar atento para não gerar nenhum dado diferente que dê origem a uma marca identificadora.\n\nA detecção de qualquer marca identificadora no espaço destinado à transcrição dos textos definitivos acarretará a anulação da prova prático-profissional e a eliminação de você. Assim, por exemplo, no fechamento da peça, você deve optar por utilizar apenas “reticências” ou “XXX”, ou seja: data “...” ou Data “XXX”, local “...” ou Local “XXX”, Advogado “...” ou Advogado “XXX”, inscrição OAB “...” ou Inscrição OAB “XXX”, destacando-se que, no corpo das respostas, você não deverá criar nenhum dado gerador de marca de identificação.\n\n# OBSERVAÇÕES\n\nPEÇA PRÁTICO-PROFISSIONAL: A peça deve abranger todos os fundamentos de Direito que possam ser utilizados para dar respaldo à pretensão. A simples menção ou transcrição do dispositivo legal não confere pontuação.\n\nQUESTÃO: Você deve fundamentar suas respostas. A mera citação do dispositivo legal não confere pontuação.\n\nA partir de agora, todas as suas respostas comporão o texto definitivo (não o caderno de rascunhos).\n"
}
```
