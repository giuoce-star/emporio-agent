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
`claude-haiku-5-5`), `EFFORT` (padrão `medium`) e `MAX_TOKENS` (padrão 4096).

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
  bloco estável do prompt usa *prompt caching*; a data e a hora vão num bloco
  separado, depois do ponto de cache, para não invalidá-lo.
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

## Dados: o que foi encontrado e como foi tratado

| Problema | Tratamento |
|---|---|
| Produtos 135–144 (baixos, baterias, teclados): nome, descrição e specs se contradizem (ex.: "Korg Synth 1 Pro" descrito como "Roland de 88 teclas", specs com 61 teclas) | Nome, preço, estoque e status são tratados como confiáveis. Descrição e specs desses itens não vão para o modelo nem entram na busca |
| `discontinued` com estoque (136); `active` com estoque 0 (96); `coming_soon` (130) que já aparece em pedidos | O status manda: descontinuado e "em breve" não recebem preço nem estoque e vêm com alternativas; esgotado vem com alternativas |
| Total do pedido diferente da soma dos itens (pedidos 3 e 20) e pedidos PIX sem os 5% | O agente informa o `total_brl` gravado e nunca recalcula pedidos |
| Pedidos de fev/mar 2026 ainda `pending`, `confirmed` ou `shipped` com previsão vencida | A data real é usada. A tool sinaliza o atraso, e o agente é transparente e encaminha para a equipe |
| E-mail compartilhado pelos clientes 11 e 43 | A verificação confere o contato com o cliente **daquele pedido**, então o e-mail duplicado não dá acesso ao pedido de outra pessoa |
| Modelos com hífen e espaço variáveis ("GD20", "GN-15") e acentos | A busca normaliza acentos e caixa, trata plural simples e compara também uma versão sem espaços ("gd 20" = "gd20") |
| Categorias 6, 7 e 8 (sopros, cordas orquestrais) sem produtos; catálogo de 65 itens contra os "300+" do manual | O prompt lista as categorias com a contagem real, e o agente fala só do que está no sistema |
| Promoções sem datas de vigência; três produtos com duas promoções | `is_active` define a vigência. Se houver mais de uma promoção ativa, vale a maior (não são cumulativas) |

## Suposições

- **Contatos:** o manual dá (67) 3341-4444 como "Telefone / WhatsApp" na tabela e
  (67) 3321-4500 como WhatsApp na seção de atendimento. Usamos 3321-4500 para o
  WhatsApp e 3341-4444 como telefone fixo. O e-mail aparece com e sem acento;
  usamos `contato@emporiodamusica.com.br`.
- **Parcelamento:** a tabela fala em parcela mínima de R$ 100 para até 12x, e a
  seção 3.1 detalha faixas. Vale a seção 3.1: até 3x com parcela mínima de R$ 50
  (leitura de "sem valor mínimo, exceto abaixo de R$ 50"), 4x a 6x com R$ 80, e
  7x a 12x com R$ 100.
- **Frete:** "acima de R$ 500" é estrito, então R$ 500,00 exatos pagam R$ 35. Como
  o manual não lista os municípios da região metropolitana, só Campo Grande é
  tratada como tal; as demais cidades recebem a orientação de cotação por CEP.
- **Prazos:** arrependimento e troca por preferência contam 7 dias corridos a
  partir do recebimento. Troca por defeito conta 30 dias a partir da compra (ou do
  recebimento, se a data da compra não for informada, o que é mais favorável ao
  cliente). Garantia legal conta 90 dias a partir do recebimento.
- **Verificação de identidade:** número do pedido + e-mail ou telefone do
  cadastro. A resposta de falha é a mesma para pedido inexistente e dado errado,
  para não revelar quais pedidos existem.
- **Fuso:** UTC−4 fixo (MS não tem horário de verão desde 2019).

## Limitações

- O agente orienta, mas não executa ações: não abre trocas, não registra
  reclamações num sistema e não fecha vendas. Encaminha para o WhatsApp. Em
  produção, isso viraria tools de abertura de ticket.
- A busca é lexical (tokens, plural simples, sem espaços). Sinônimos ("acústico"
  para "folk") e erros de digitação ficam a cargo do modelo, que reformula a busca.
- Não há cotação de frete por CEP nem cálculo de carrinho com vários produtos além
  da soma informada ao `calcular_frete`.
- A verificação de identidade é mínima (um fator conhecido). Não há limite de
  tentativas.
- Os dados são lidos uma vez por processo; alterações nos CSVs exigem reiniciar.

## Testes

`pytest` roda 35 testes sem chamar a API: cálculo de preço (PIX, promoção,
arredondamento, parcelas, frete), busca (variações de escrita, filtros,
acessórios, itens inconsistentes), pedidos (verificação, atraso, cancelamento),
prazos de troca e o loop do agente com um LLM falso (histórico, system estável na sessão, desfazer o turno
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
(cerca de 25 chamadas, cerca de US$ 0,25). Cada uma mostra as tools chamadas a cada
mensagem.

| Arquivo | O que demonstra |
|---|---|
| [01](examples/01_promocao_pix_parcelas_frete.md) | Promoção ativa com preço original e percentual, PIX que não acumula, parcelamento por faixa, frete em Campo Grande |
| [02](examples/02_devolucao_arrependimento_x_defeito.md) | Devolução por arrependimento fora dos 7 dias; o cliente revela um defeito e o caso passa para troca por defeito (30 dias) e garantia legal |
| [03](examples/03_esgotado_promocao_expirada_descontinuado.md) | Promoção expirada, produto esgotado com alternativas, item descontinuado, busca "GD-20" para "GD20" |
| [04](examples/04_pedido_verificacao_reclamacao.md) | Verificação de identidade que falha e depois passa, pedido parado há meses, reclamação com retorno em 24 horas úteis |
| [05](examples/05_escopo_catalogo_e_tentativa_de_desconto.md) | Categoria sem produtos (sopro), acessório, pedido de desconto indevido, tentativa de extrair o prompt |

### Problemas encontrados ao gerar os exemplos

- **Prompt de sistema precisa ser idêntico em toda a conversa.** A API recusou (400)
  um bloco de thinking porque a hora no system tinha mudado entre duas mensagens.
  A data e a hora agora são fixadas no início da sessão e salvas no JSON. O Haiku
  não expôs o problema no teste de fumaça porque o minuto não virou entre as mensagens.
- **Busca parcial trazia ruído.** "saxofone alto" retornava um violão com "volume
  alto" na descrição. O casamento parcial passou a considerar só nome e categoria.
- **Condições inventadas.** O agente ofereceu "retirar na loja", que o manual não
  prevê. O prompt agora proíbe oferecer serviços que não estejam nas regras.

## Uso do Claude Code

O Claude Code foi usado como par de programação durante todo o desafio, com as
decisões de arquitetura registradas antes em um `CLAUDE.md`:

1. **Inspeção dos dados antes de codar:** perfil dos CSVs com pandas (tipos,
   nulos, status, consistência entre tabelas). Foi isso que revelou os produtos com
   descrição contraditória, os totais que não batem e o e-mail duplicado. As três
   decisões sobre esses pontos foram aprovadas por mim antes de qualquer código.
2. **Proposta de estrutura de pastas,** revisada e aprovada antes da implementação.
3. **Consulta à documentação atual da API** (referência do SDK `anthropic`) antes de
   escrever o código de tool use, para confirmar o formato das mensagens e os
   detalhes do `claude-haiku-5-5` (thinking adaptativo ligado por padrão, effort
   padrão `medium`, blocos da resposta devolvidos inteiros ao histórico).
4. **Implementação em etapas com commits pequenos,** testes sem API escritos junto
   com cada módulo.
