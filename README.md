# Empório da Música — agente de atendimento

Agente de mensagens de texto, em Python, para a Empório da Música, loja fictícia de
instrumentos musicais em Campo Grande (MS). Ele responde no tom da loja, consulta o
catálogo e os pedidos (CSVs em `data/`), aplica as políticas do manual interno
(`data/politicas_da_loja.pdf`) e trata perguntas fora de escopo.

## Como rodar

Requer Python 3.11+.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows (no Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env        # e preencha ANTHROPIC_API_KEY
python main.py                # nova conversa
python main.py --debug        # mostra as tools chamadas e o uso de tokens
python main.py --sessao ID    # retoma uma conversa salva em sessions/ID.json
pytest                        # testes (não chamam a API)
```

Variáveis do `.env`: `ANTHROPIC_API_KEY` (obrigatória), `MODEL` (padrão
`claude-haiku-5-5`), `EFFORT` (padrão `medium`), `MAX_TOKENS` (padrão 4096) e
`REFERENCE_DATE` (data usada como "hoje", AAAA-MM-DD; vazia = data real).

## Arquitetura

```
main.py              CLI
agente/
  agente.py          loop: mensagem -> modelo -> tools -> resultados -> resposta
  llm.py             único arquivo que fala com a API da Anthropic
  prompt.py          persona, regras e o manual inteiro no prompt de sistema
  politicas.py       extração do texto do PDF
  tools.py           tools do modelo (schemas + implementação)
  precos.py          promoção, PIX, parcelamento e frete (Decimal, funções puras)
  dados.py           carga e normalização dos CSVs
  sessao.py          histórico em memória + sessions/<id>.json
tests/               testes sem chamada à API
examples/            conversas de exemplo
```

### Decisões e justificativas

- **Function calling nativo, sem LangChain/LangGraph.** O fluxo é um loop curto
  (mensagem, tool calls, resultados, resposta). Um framework acrescentaria
  dependências e camadas de abstração sem resolver nenhum problema que o loop
  de cerca de 40 linhas em `agente.py` não resolva. O loop é manual, e não o
  Tool Runner do SDK, para não depender de uma API beta.
- **Contas em código, nunca no modelo.** Preço promocional, desconto PIX,
  parcelamento, frete e prazos de troca são calculados em Python, com `Decimal` e
  arredondamento meio-para-cima, e chegam ao modelo já formatados
  ("R$ 1.967,18"). O prompt manda repassar os valores sem refazer conta. Modelos
  erram aritmética e datas com frequência, e preço errado pode configurar
  propaganda enganosa (o próprio manual diz isso).
- **Manual inteiro no prompt, sem RAG.** São 8 páginas, cerca de 11 mil
  caracteres. Cabe com folga no contexto, e o modelo vê todas as regras ao mesmo
  tempo, o que importa porque elas se cruzam (promoção × PIX, defeito × garantia).
  RAG traria o risco de recuperar só parte de uma regra, sem ganho de precisão. O
  bloco estável do prompt usa *prompt caching*. A data e a hora vão num bloco
  separado, depois do ponto de cache, fixadas no início da sessão: a API recusa
  blocos de thinking se o system mudar no meio da conversa.
- **Regras críticas também reescritas no prompt.** Além do manual bruto, o
  prompt resume as regras de maior risco (separação arrependimento × defeito ×
  garantia, PIX × promoção, escopo, verificação de pedido) e resolve as
  inconsistências do manual explicitamente.
- **Cinco tools pequenas, cada uma com uma responsabilidade:** `buscar_produtos`,
  `consultar_preco`, `calcular_frete`, `prazos_troca_devolucao`, `status_pedido`.
  O CLAUDE.md previa três. `calcular_frete` e `prazos_troca_devolucao` entraram
  pelo mesmo motivo das contas: frete e contagem de dias são regras
  determinísticas que o modelo erraria.
- **Provedor isolado em `llm.py`.** O loop só conhece `LLM.responder` e os
  construtores de mensagem. Trocar de provedor significa reescrever esse arquivo.
- **Modelo:** `claude-haiku-5-5` no desenvolvimento, por custo (orçamento de US$ 5).
  `claude-sonnet-5-5` fica para a validação final dos cenários difíceis e para as
  conversas de exemplo. É configurável por `MODEL`.
- **Reclamação sem tool.** A resposta é padronizada pelo prompt (empatia, pedido
  dos dados, retorno em 24 horas úteis). A conversa fica salva no JSON da sessão.
- **Provedor: Anthropic.** Tool use nativo na API e SDK Python oficial (`anthropic`).
  Como a chamada ao modelo fica isolada em `llm.py`, a escolha é reversível: trocar
  de provedor significa reescrever esse arquivo.
- **Interface: CLI.** O enunciado diz que o foco é o agente, então a interface ficou
  no mínimo. A CLI mostra as tools chamadas com `--debug` e retoma uma conversa com
  `--sessao`.
- **Persistência: JSON por sessão.** Permite retomar a conversa, não exige banco em
  um protótipo, e a conversa salva serve de registro da reclamação. O trade-off é
  não ter busca nem concorrência.
- **Persona e tom.** O prompt traduz o tom do manual em um assistente virtual
  "informal, mas profissional: um amigo que entende de música": acolhedor, direto,
  sem linguagem robótica nem formal demais, com mensagens curtas, como num chat. O
  agente aplica as regras como "nossa política", sem citar o manual, não oferece
  serviços ou condições fora das regras e não opina sobre produto sem base na
  descrição ou nas specs.

## Suposições e inconsistências dos dados

Os dados de `data/` são fictícios, estáticos e **a fonte de verdade**: os CSVs não
são alterados. Três princípios guiam o tratamento:

1. **Nada é corrigido em silêncio.** O agente informa o que consta no sistema e,
   quando é relevante para o cliente, diz que a equipe confirma pelo WhatsApp.
2. **Defesa no código onde o modelo poderia errar.** As tools sinalizam a
   inconsistência junto com o dado (`aviso_cadastro`, `aviso_estoque`,
   `divergencias_no_cadastro`) e dizem como tratá-la.
3. **"Hoje" é configurável.** `REFERENCE_DATE` no `.env` (AAAA-MM-DD) define a data
   usada no atraso de entrega, nos prazos de troca e devolução e na data informada
   ao modelo. Vazia, vale a data real. As promoções não têm data no CSV, então a
   vigência delas é decidida só por `is_active`, e `REFERENCE_DATE` não as afeta.

Linhas contam o cabeçalho do CSV como linha 1.

### products.csv

| Linha | O que está estranho | Tratamento |
|---|---|---|
| 57–66 (ids 135–144) | Nome, descrição e specs se contradizem. Exemplos: o 142 "Korg Synth 1 Pro" tem descrição de um Roland de 88 teclas e specs com 61 teclas; o 137 "Yamaha Bass 3X" tem "5 cordas Ibanez" na descrição e `strings: 4`; o 139 "Yamaha Kit 1" tem descrição de uma Pearl Export | Descrição e specs não vão para o modelo nem entram na busca. `buscar_produtos` apenas omite a descrição desses itens, sem aviso. `consultar_preco` devolve `aviso_cadastro`: o agente informa só nome, preço e disponibilidade e, se o cliente perguntar das especificações, diz que não consegue explicar a divergência e indica a equipe pelo WhatsApp, sem levantar hipóteses |
| 58 (id 136) | `discontinued` com 13 unidades em estoque | O status prevalece: o item não é oferecido e vem com alternativas. `aviso_estoque` faz o agente dizer o que consta, se o cliente insistir |
| 51 (id 130) | `coming_soon` com 2 em estoque, e já aparece nos pedidos 3 (entregue) e 14 | Igual ao 136. Nos pedidos, o item aparece normalmente, com uma divergência registrada |
| 5 (id 84) | Nome truncado: "Giannini GN-15 Nylon Cedr Natural" | Mantido exatamente como está. O prompt proíbe completar ou corrigir nomes |
| 52 (id 145) | Fora de ordem no arquivo (vem antes do 131) | Sem efeito |
| coluna `specs` | `strings` muda de sentido (`nylon`/`steel` em violões, `"6"`/`"4"` em guitarras e baixos). Cores em PT e EN (`Preto` nas linhas 10 e 25, `Black` em outras) | Repassado como está; sem impacto nas regras |
| 17 (id 96) | `active` com estoque 0 | Não é erro: é "esgotado", com alternativas |

### categories.csv

| Linha | O que está estranho | Tratamento |
|---|---|---|
| 7–9 | Sopros (madeiras e metais) e cordas orquestrais não têm nenhum produto | O prompt lista a contagem real por categoria; o agente diz que não há itens cadastrados |
| 3 | Baixos "elétricos e acústicos", mas não há baixo acústico | Fala só do que a busca retorna |

### promotions.csv

| Linha | O que está estranho | Tratamento |
|---|---|---|
| todas | Não há datas de vigência, só `is_active` | A vigência é `is_active`. Promoções inativas aparecem como "encerradas" quando o cliente pergunta |
| 7/24, 9/23, 10/26 | Produtos 93, 96 e 99 têm duas promoções cada (todas inativas) | Se houver mais de uma ativa, vale a maior (não são cumulativas) |
| 2, 18 | Black Friday com 10% (o manual diz 15–30%); Aniversário com 30% (o manual diz 10–25%) | Ambas inativas, sem efeito |

### orders.csv e order_items.csv

| Linha | O que está estranho | Tratamento |
|---|---|---|
| orders 4 e 21 (pedidos 3 e 20) | O total gravado não bate com a soma dos itens pelos preços atuais (3450 contra 3498; 1400 contra 1488). `order_items` não guarda preço unitário | Repassa o total gravado e registra a divergência. O agente só a menciona se o cliente questionar o valor |
| orders 2, 6, 11, 14, 18 (pedidos 1, 5, 10, 13, 17) | Pedidos no PIX pelo preço de tabela, sem os 5% | Mesmo tratamento |
| orders 10, 17, 19 (pedidos 9, 16, 18) | Parcela abaixo do mínimo atual: 6x de R$ 58,32, 6x de R$ 71,65 e 12x de R$ 38,33 | Informa a forma de pagamento gravada; registra a divergência |
| orders 2–6 e 8–9 (pedidos 1–5, 7 e 8) | Pedidos de Campo Grande com rastreio dos Correios e previsão de 10 a 15 dias, quando o manual diz motoboy em 1 a 3 dias úteis | Informa o rastreio e a previsão gravados, sem afirmar qual modalidade foi usada |
| orders 9–17 | Datas de fev/mar 2026 com status em aberto; contra a data real, tudo está muito atrasado | `REFERENCE_DATE` permite avaliar contra outra data. A tool sinaliza atraso e o agente orienta o WhatsApp |

### customers.csv

| Linha | O que está estranho | Tratamento |
|---|---|---|
| 12 e 44 | Clientes 11 e 43 com o mesmo e-mail | A verificação confere o contato com o cliente **daquele pedido**, então ninguém vê pedido de outra pessoa |
| 32–51 | Nomes sem acento ("Joao", "Leticia") | Sem impacto: a verificação usa e-mail ou telefone |

### Manual de políticas (PDF)

| Ponto | Suposição |
|---|---|
| (67) 3341-4444 aparece como "Telefone / WhatsApp" e (67) 3321-4500 como o WhatsApp | 3321-4500 para o WhatsApp, 3341-4444 como telefone fixo |
| E-mail com e sem acento | `contato@emporiodamusica.com.br` |
| A tabela diz parcela mínima de R$ 100 até 12x; a seção 3.1 detalha faixas | Vale a 3.1: até 3x com mínimo de R$ 50 (leitura de "sem valor mínimo, exceto abaixo de R$ 50"), 4x a 6x com R$ 80, 7x a 12x com R$ 100 |
| "Frete grátis acima de R$ 500"; municípios da região metropolitana não listados | R$ 500,00 exatos pagam R$ 35. Só Campo Grande conta como metropolitana; as demais cidades recebem a orientação de cotação por CEP |
| Arrependimento vale só para "compras online", mas os pedidos não dizem o canal | O agente pergunta ao cliente; na dúvida, a equipe confirma |
| "Venda final" em liquidação não é elegível para troca, mas nenhum dado marca isso | O agente avisa que a equipe confirma a elegibilidade |
| Prazo da troca por preferência ("até 7 dias") não diz a partir de quando | Conta a partir do recebimento, como o arrependimento |
| Catálogo de "300+" instrumentos, incluindo sopros e cordas orquestrais | O sistema tem 65 itens; o agente fala só do que está nele |

### Outras suposições

- **Prazos:** arrependimento e troca por preferência contam 7 dias corridos a
  partir do recebimento. Troca por defeito conta 30 dias a partir da compra (ou do
  recebimento, se a data da compra não for informada, o que é mais favorável ao
  cliente). Garantia legal conta 90 dias a partir do recebimento.
- **Verificação de identidade:** número do pedido + e-mail ou telefone do
  cadastro. A resposta de falha é a mesma para pedido inexistente e dado errado,
  para não revelar quais pedidos existem.
- **Fuso:** UTC−4 fixo (MS não tem horário de verão desde 2019). Com
  `REFERENCE_DATE` definida, o modelo recebe só a data, sem hora.

## Limitações

- O agente orienta, mas não executa ações: não abre trocas, não registra
  reclamações num sistema e não fecha vendas. Indica o WhatsApp para isso. Em
  produção, isso viraria tools de abertura de ticket.
- A busca é lexical (tokens, plural simples, sem espaços). Sinônimos ("acústico"
  para "folk") e erros de digitação ficam a cargo do modelo, que reformula a busca.
- Não há cotação de frete por CEP nem cálculo de carrinho com vários produtos além
  da soma informada ao `calcular_frete`.
- A verificação de identidade é mínima (um fator conhecido). Não há limite de
  tentativas.
- Os dados são lidos uma vez por processo; alterações nos CSVs exigem reiniciar.

## Com mais tempo

- **Avaliação automatizada:** cenários com resultado esperado (preço, PIX ×
  promoção, prazos de troca, escopo) para comparar Haiku e Sonnet e pegar
  regressões de prompt.
- **Observabilidade:** registrar por conversa as tools chamadas, tokens, custo,
  encaminhamentos e perguntas sem resposta, para achar lacunas no manual e no
  catálogo.
- **Tools que executam ações:** abrir ticket real de troca ou reclamação, em vez de
  orientar o cliente a chamar o WhatsApp.
- **Canal real:** integração com o WhatsApp, principal meio de atendimento segundo o
  manual.
- **Busca semântica no catálogo,** mantendo preço e estoque determinísticos (vindos
  das tools, nunca do modelo).
- **Frete e carrinho:** cotação por CEP via API de transportadora e carrinho com
  vários produtos.
- **Tom adaptado ao nível do cliente** (iniciante ou profissional), a partir do que
  ele diz na conversa, sem guardar perfil.
- **Infraestrutura:** dados em banco em vez de CSV, verificação de identidade mais
  forte com limite de tentativas e transferência para atendente humano.

## Testes

`pytest` roda 56 testes sem chamar a API: cálculo de preço (PIX, promoção,
arredondamento, parcelas, frete), busca (variações de escrita, filtros,
acessórios, itens inconsistentes), pedidos (verificação, atraso, cancelamento),
prazos de troca, tratamento das inconsistências dos dados e `REFERENCE_DATE`, e o loop do agente com um LLM falso (histórico, system estável na sessão, desfazer o turno
em erro da API, limite de rodadas).

### Teste de fumaça com o modelo

Uma conversa de 5 mensagens com `claude-haiku-5-5` (promoção + PIX, acessório,
pedido com verificação e atraso, pergunta fora de escopo) se comportou como
esperado: o PIX não foi somado à promoção, o pedido só foi consultado depois do
e-mail e o cache do prompt foi reaproveitado entre as chamadas. Um defeito
apareceu e foi corrigido: no pedido atrasado, o agente dizia "posso encaminhar
para a equipe", algo que ele não faz. O prompt e o alerta da tool passaram a
orientar o cliente a falar pelo WhatsApp.

## Conversas de exemplo

Geradas com `claude-sonnet-5-5` por `examples/gerar_exemplos.py`, que chama a API
(cerca de 25 chamadas, cerca de US$ 0,25; `python examples/gerar_exemplos.py 01` gera
só uma). Cada uma mostra as tools chamadas a cada mensagem e a data usada como "hoje".

| Arquivo | O que demonstra |
|---|---|
| [01](examples/01_promocao_pix_parcelas_frete.md) | Informações gerais da loja, promoção ativa, PIX, parcelamento e frete |
| [02](examples/02_devolucao_arrependimento_x_defeito.md) | Devolução por arrependimento fora dos 7 dias; o cliente revela um defeito e o caso passa para troca por defeito (30 dias) e garantia legal |
| [03](examples/03_esgotado_promocao_expirada_descontinuado.md) | Promoção expirada, produto esgotado com alternativas, item descontinuado com outros violões de 7 cordas, preço de produto sem promoção ativa |
| [04](examples/04_pedido_verificacao_reclamacao.md) | Verificação de identidade que falha e depois passa, pedido parado há meses, reclamação com retorno em 24 horas úteis |
| [05](examples/05_escopo_catalogo_e_tentativa_de_desconto.md) | Categoria sem produtos (sopro), acessório, pedido de desconto indevido, tentativa de extrair o prompt |

### Problemas encontrados ao gerar os exemplos

- **Prompt de sistema precisa ser idêntico em toda a conversa.** A API recusou (400)
  um bloco de thinking porque a hora no system tinha mudado entre duas mensagens.
  A data e a hora agora são fixadas no início da sessão e salvas no JSON. O problema
  não apareceu no teste de fumaça com o Haiku.
- **Busca parcial trazia ruído.** "saxofone alto" retornava um violão com "volume
  alto" na descrição. O casamento parcial passou a considerar só nome e categoria.
- **Condições inventadas.** O agente ofereceu "retirar na loja", que o manual não
  prevê. O prompt agora proíbe oferecer serviços que não estejam nas regras.

## Uso de assistentes de código

Usei o Claude em dois lugares. No chat (claude.ai), para planejar: discuti a
arquitetura, o escopo para o prazo de um dia, o provedor e o custo, montei o
CLAUDE.md com as decisões, redigido com o Claude no chat, e revisei as entregas. No Claude Code, para implementar:
ele inspecionou os dados, propôs a estrutura, escreveu o código e os testes e fez
os commits.

O Claude Code foi usado como par de programação durante todo o desafio, com as
decisões de arquitetura registradas antes em um `CLAUDE.md`:

1. **Inspeção dos dados antes de codar:** perfil dos CSVs com pandas (tipos,
   nulos, status, consistência entre tabelas). Foi isso que revelou os produtos com
   descrição contraditória, os totais que não batem e o e-mail duplicado. As três
   decisões sobre esses pontos foram aprovadas por mim antes de qualquer código.
2. **Proposta de estrutura de pastas,** revisada e aprovada antes da implementação.
3. **Consulta à referência da API da Anthropic embutida no Claude Code** (skill
   `claude-api`) antes de escrever o código de tool use, para confirmar o formato
   das mensagens e os detalhes do `claude-haiku-5-5` (thinking adaptativo ligado
   por padrão, effort padrão `medium`, blocos da resposta devolvidos inteiros ao
   histórico). O site docs.claude.com não foi consultado diretamente.
   Depois, um erro 400 da API mostrou que ela valida os blocos de thinking contra o
   prompt de sistema.
4. **Implementação em etapas com commits pequenos,** testes sem API escritos junto
   com cada módulo.
5. **Revisão manual das saídas:** conversei com o agente pela CLI e li as
   conversas de exemplo antes de aceitá-las. Isso levou a correções no código e
   no prompt: ordenação dos resultados por preço, opinião sobre produto só com
   base na descrição e nas specs, não sugerir exceção de prazo e não prometer
   canal de retorno.
