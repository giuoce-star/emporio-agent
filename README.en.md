English version of README.md, prepared for the case submission.

# Empório da Música — customer service agent

Text messaging agent, in Python, for Empório da Música, a fictional musical
instrument store in Campo Grande (MS, Brazil). It replies in the store's tone, queries
the catalog and orders (CSVs in `data/`), applies the policies from the internal manual
(`data/politicas_da_loja.pdf`) and handles out-of-scope questions.

## How to run

Requires Python 3.11+.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows (on Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env        # and fill in ANTHROPIC_API_KEY
python main.py                # new conversation
python main.py --debug        # shows the tools called and token usage
python main.py --sessao ID    # resumes a conversation saved in sessions/ID.json
pytest                        # tests (do not call the API)
```

`.env` variables: `ANTHROPIC_API_KEY` (required), `MODEL` (default
`claude-haiku-5-5`), `EFFORT` (default `medium`), `MAX_TOKENS` (default 4096) and
`REFERENCE_DATE` (date used as "today", YYYY-MM-DD; empty = real date).

## Architecture

```
main.py              CLI
agente/
  agente.py          loop: message -> model -> tools -> results -> reply
  llm.py             the only file that talks to the Anthropic API
  prompt.py          persona, rules and the entire manual in the system prompt
  politicas.py       text extraction from the PDF
  tools.py           model tools (schemas + implementation)
  precos.py          promotion, PIX, installments and shipping (Decimal, pure functions)
  dados.py           CSV loading and normalization
  sessao.py          in-memory history + sessions/<id>.json
tests/               tests with no API calls
examples/            example conversations
```

### Decisions and rationale

- **Native function calling, no LangChain/LangGraph.** The flow is a short loop
  (message, tool calls, results, reply). A framework would add dependencies and
  layers of abstraction without solving any problem that the roughly 40-line loop
  in `agente.py` does not solve. The loop is manual, rather than the SDK's Tool
  Runner, to avoid depending on a beta API.
- **Calculations in code, never in the model.** Promotional price, PIX discount,
  installments, shipping and exchange deadlines are calculated in Python, with
  `Decimal` and round-half-up, and reach the model already formatted
  ("R$ 1.967,18"). The prompt instructs it to pass the values along without redoing
  the math. Models often get arithmetic and dates wrong, and a wrong price can
  amount to false advertising (the manual itself says so).
- **Entire manual in the prompt, no RAG.** It is 8 pages, about 11 thousand
  characters. It fits comfortably in the context, and the model sees all the rules
  at once, which matters because they intersect (promotion × PIX, defect ×
  warranty). RAG would bring the risk of retrieving only part of a rule, with no
  gain in accuracy. The stable block of the prompt uses *prompt caching*. The date
  and time go in a separate block, after the cache breakpoint, fixed at the start
  of the session: the API rejects thinking blocks if the system prompt changes in
  the middle of the conversation.
- **Critical rules also rewritten in the prompt.** Besides the raw manual, the
  prompt summarizes the highest-risk rules (separating change-of-mind return ×
  defect × warranty, PIX × promotion, scope, order verification) and resolves the
  manual's inconsistencies explicitly.
- **Five small tools, each with one responsibility:** `buscar_produtos`,
  `consultar_preco`, `calcular_frete`, `prazos_troca_devolucao`, `status_pedido`.
  CLAUDE.md planned for three. `calcular_frete` and `prazos_troca_devolucao` were
  added for the same reason as the calculations: shipping and day counting are
  deterministic rules that the model would get wrong.
- **Provider isolated in `llm.py`.** The loop only knows `LLM.responder` and the
  message constructors. Switching providers means rewriting that file.
- **Model:** `claude-haiku-5-5` during development, for cost reasons (US$ 5 budget).
  `claude-sonnet-5-5` is reserved for the final validation of the hard scenarios and
  for the example conversations. It is configurable through `MODEL`.
- **Complaints without a tool.** The reply is standardized by the prompt (empathy,
  asking for the details, follow-up within 24 business hours). The conversation is
  saved in the session JSON.
- **Provider: Anthropic.** Native tool use in the API and an official Python SDK
  (`anthropic`). Since the model call is isolated in `llm.py`, the choice is
  reversible: switching providers means rewriting that file.
- **Interface: CLI.** The brief says the focus is the agent, so the interface was kept
  minimal. The CLI shows the tools called with `--debug` and resumes a conversation
  with `--sessao`.
- **Persistence: JSON per session.** It allows resuming the conversation, requires no
  database for a prototype, and the saved conversation serves as the record of the
  complaint. The trade-off is having no search and no concurrency.
- **Persona and tone.** The prompt turns the manual's tone into a virtual assistant
  that is "informal but professional: a friend who knows about music": welcoming,
  direct, neither robotic nor too formal, with short messages, like in a chat. The
  agent applies the rules as "nossa política" (our policy), without citing the manual,
  does not offer services or conditions outside the rules, and does not give opinions
  about a product without a basis in the description or specs.

## Assumptions and data inconsistencies

The data in `data/` is fictional, static and **the source of truth**: the CSVs are
not altered. Three principles guide how it is handled:

1. **Nothing is silently corrected.** The agent reports what is in the system and,
   when relevant to the customer, says the team will confirm via WhatsApp.
2. **Defense in code where the model could go wrong.** The tools flag the
   inconsistency along with the data (`aviso_cadastro`, `aviso_estoque`,
   `divergencias_no_cadastro`) and say how to handle it.
3. **"Today" is configurable.** `REFERENCE_DATE` in `.env` (YYYY-MM-DD) sets the date
   used for delivery delays, for exchange and return deadlines and for the date
   given to the model. Empty, the real date applies. Promotions have no date in the
   CSV, so their validity is decided only by `is_active`, and `REFERENCE_DATE` does
   not affect them.

Line numbers count the CSV header as line 1.

### products.csv

| Line | What looks wrong | Handling |
|---|---|---|
| 57–66 (ids 135–144) | Name, description and specs contradict each other. Examples: 142 "Korg Synth 1 Pro" has the description of an 88-key Roland and specs with 61 keys; 137 "Yamaha Bass 3X" has "5 cordas Ibanez" in the description and `strings: 4`; 139 "Yamaha Kit 1" has the description of a Pearl Export | Description and specs do not go to the model and are not searched. `buscar_produtos` just omits the description of these items, with no warning. `consultar_preco` returns `aviso_cadastro`: the agent reports only name, price and availability and, if the customer asks about the specifications, says it cannot explain the discrepancy and points to the team on WhatsApp, without speculating |
| 58 (id 136) | `discontinued` with 13 units in stock | The status prevails: the item is not offered and comes with alternatives. `aviso_estoque` makes the agent state what is on record, if the customer insists |
| 51 (id 130) | `coming_soon` with 2 in stock, and it already appears in orders 3 (delivered) and 14 | Same as 136. In orders, the item appears normally, with a discrepancy recorded |
| 5 (id 84) | Truncated name: "Giannini GN-15 Nylon Cedr Natural" | Kept exactly as is. The prompt forbids completing or correcting names |
| 52 (id 145) | Out of order in the file (comes before 131) | No effect |
| `specs` column | `strings` changes meaning (`nylon`/`steel` for acoustic guitars, `"6"`/`"4"` for electric guitars and basses). Colors in PT and EN (`Preto` on lines 10 and 25, `Black` on others) | Passed along as is; no impact on the rules |
| 17 (id 96) | `active` with stock 0 | Not an error: it is "esgotado" (out of stock), with alternatives |

### categories.csv

| Line | What looks wrong | Handling |
|---|---|---|
| 7–9 | Woodwinds, brass and orchestral strings have no products at all | The prompt lists the real count per category; the agent says there are no items registered |
| 3 | Basses "elétricos e acústicos" (electric and acoustic), but there is no acoustic bass | It only talks about what the search returns |

### promotions.csv

| Line | What looks wrong | Handling |
|---|---|---|
| all | There are no validity dates, only `is_active` | Validity is `is_active`. Inactive promotions appear as "encerradas" (ended) when the customer asks |
| 7/24, 9/23, 10/26 | Products 93, 96 and 99 have two promotions each (all inactive) | If more than one is active, the largest applies (they are not cumulative) |
| 2, 18 | Black Friday at 10% (the manual says 15–30%); Store Anniversary at 30% (the manual says 10–25%) | Both inactive, no effect |

### orders.csv and order_items.csv

| Line | What looks wrong | Handling |
|---|---|---|
| orders 4 and 21 (orders 3 and 20) | The recorded total does not match the sum of the items at current prices (3450 versus 3498; 1400 versus 1488). `order_items` does not store a unit price | Passes along the recorded total and records the discrepancy. The agent only mentions it if the customer questions the amount |
| orders 2, 6, 11, 14, 18 (orders 1, 5, 10, 13, 17) | PIX orders at list price, without the 5% | Same handling |
| orders 10, 17, 19 (orders 9, 16, 18) | Installment below the current minimum: 6x of R$ 58,32, 6x of R$ 71,65 and 12x of R$ 38,33 | Reports the recorded payment method; records the discrepancy |
| orders 2–6 and 8–9 (orders 1–5, 7 and 8) | Campo Grande orders with Correios tracking and an estimate of 10 to 15 days, when the manual says motorcycle courier in 1 to 3 business days | Reports the recorded tracking and estimate, without stating which delivery method was used |
| orders 9–17 | Feb/Mar 2026 dates with open status; against the real date, everything is very late | `REFERENCE_DATE` allows evaluating against another date. The tool flags the delay and the agent points to WhatsApp |

### customers.csv

| Line | What looks wrong | Handling |
|---|---|---|
| 12 and 44 | Customers 11 and 43 with the same e-mail | Verification checks the contact against the customer of **that order**, so nobody sees another person's order |
| 32–51 | Names without accents ("Joao", "Leticia") | No impact: verification uses e-mail or phone |

### Policy manual (PDF)

| Point | Assumption |
|---|---|
| (67) 3341-4444 appears as "Telefone / WhatsApp" and (67) 3321-4500 as the WhatsApp number | 3321-4500 for WhatsApp, 3341-4444 as the landline |
| E-mail with and without an accent | `contato@emporiodamusica.com.br` |
| The table says a minimum installment of R$ 100 for up to 12x; section 3.1 details tiers | Section 3.1 applies: up to 3x with a R$ 50 minimum (reading of "no minimum, except below R$ 50"), 4x to 6x with R$ 80, 7x to 12x with R$ 100 |
| "Free shipping above R$ 500"; municipalities of the metropolitan region not listed | Exactly R$ 500,00 pays R$ 35. Only Campo Grande counts as metropolitan; other cities are told to get a quote by postal code (CEP) |
| Change-of-mind return applies only to "online purchases", but orders do not state the channel | The agent asks the customer; when in doubt, the team confirms |
| "Final sale" in clearance is not eligible for exchange, but no data marks this | The agent says the team will confirm eligibility |
| The preference exchange deadline ("up to 7 days") does not say from when | It counts from receipt, like the change-of-mind return |
| Catalog of "300+" instruments, including wind instruments and orchestral strings | The system has 65 items; the agent only talks about what is in it |

### Other assumptions

- **Deadlines:** change-of-mind return and preference exchange count 7 calendar days
  from receipt. Defect exchange counts 30 days from purchase (or from receipt, if the
  purchase date is not provided, which is more favorable to the customer). Statutory
  warranty counts 90 days from receipt.
- **Identity verification:** order number + e-mail or phone on file. The failure
  response is the same for a nonexistent order and for wrong data, so as not to reveal
  which orders exist.
- **Time zone:** fixed UTC−4 (MS has had no daylight saving time since 2019). With
  `REFERENCE_DATE` set, the model receives only the date, with no time.

## Limitations

- The agent guides but does not perform actions: it does not open exchanges, does not
  record complaints in a system and does not close sales. It points the customer to WhatsApp for that. In
  production, this would become ticket-opening tools.
- Search is lexical (tokens, simple plurals, no spaces). Synonyms ("acústico" for
  "folk") and typos are left to the model, which rephrases the search.
- There is no shipping quote by postal code (CEP), nor a calculation for a cart with
  several products beyond the sum given to `calcular_frete`.
- Identity verification is minimal (one known factor). There is no attempt limit.
- The data is read once per process; changes to the CSVs require a restart.

## With more time

- **Automated evaluation:** scenarios with expected results (price, PIX × promotion,
  exchange deadlines, scope) to compare Haiku and Sonnet and catch prompt regressions.
- **Observability:** log per conversation the tools called, tokens, cost, referrals
  and unanswered questions, to find gaps in the manual and the catalog.
- **Tools that perform actions:** open a real exchange or complaint ticket, instead of
  telling the customer to contact WhatsApp.
- **Real channel:** integration with WhatsApp, the main service channel according to
  the manual.
- **Semantic search in the catalog,** keeping price and stock deterministic (coming
  from the tools, never from the model).
- **Shipping and cart:** quote by postal code (CEP) via a carrier API and a cart with
  several products.
- **Tone adapted to the customer's level** (beginner or professional), based on what
  they say in the conversation, without storing a profile.
- **Infrastructure:** data in a database instead of CSV, stronger identity verification
  with an attempt limit, and handoff to a human agent.

## Tests

`pytest` runs 56 tests without calling the API: price calculation (PIX, promotion,
rounding, installments, shipping), search (spelling variations, filters, accessories,
inconsistent items), orders (verification, delay, cancellation), exchange deadlines,
handling of data inconsistencies and `REFERENCE_DATE`, and the agent loop with a fake
LLM (history, stable system prompt across the session, undoing the turn on an API
error, round limit).

### Smoke test with the model

A 5-message conversation with `claude-haiku-5-5` (promotion + PIX, accessory, order with
verification and delay, out-of-scope question) behaved as expected: PIX was not added
on top of the promotion, the order was only looked up after the e-mail, and the prompt
cache was reused across calls. One defect appeared and was fixed: on the delayed order,
the agent said "posso encaminhar para a equipe" (I can forward this to the team),
something it does not do. The prompt and the tool's alert now tell the customer to
reach out via WhatsApp.

## Example conversations

Generated with `claude-sonnet-5-5` by `examples/gerar_exemplos.py`, which calls the API
(about 25 calls, about US$ 0,25; `python examples/gerar_exemplos.py 01` generates just
one). Each one shows the tools called at each message and the date used as "today".

| File | What it demonstrates |
|---|---|
| [01](examples/01_promocao_pix_parcelas_frete.md) | General store information, active promotion, PIX, installments and shipping |
| [02](examples/02_devolucao_arrependimento_x_defeito.md) | Change-of-mind return outside the 7 days; the customer reveals a defect and the case moves to defect exchange (30 days) and statutory warranty |
| [03](examples/03_esgotado_promocao_expirada_descontinuado.md) | Expired promotion, out-of-stock product with alternatives, discontinued item with other 7-string acoustic guitars, price of a product with no active promotion |
| [04](examples/04_pedido_verificacao_reclamacao.md) | Identity verification that fails and then passes, order stuck for months, complaint with follow-up within 24 business hours |
| [05](examples/05_escopo_catalogo_e_tentativa_de_desconto.md) | Category with no products (wind), accessory, improper discount request, attempt to extract the prompt |

### Problems found while generating the examples

- **The system prompt must be identical throughout the conversation.** The API rejected
  (400) a thinking block because the time in the system prompt had changed between two
  messages. The date and time are now fixed at the start of the session and saved in the
  JSON. The problem did not appear in the smoke test with Haiku.
- **Partial search brought noise.** "saxofone alto" returned an acoustic guitar with
  "volume alto" in its description. Partial matching now considers only name and
  category.
- **Invented conditions.** The agent offered "retirar na loja" (store pickup), which the
  manual does not provide for. The prompt now forbids offering services that are not in
  the rules.

## Use of coding assistants

I used Claude in two places. In the chat (claude.ai), for planning: I discussed the
architecture, the scope for the one-day deadline, the provider and the cost, put
together CLAUDE.md with the decisions, drafted with Claude in the chat, and reviewed the
deliverables. In Claude Code, for implementation: it inspected the data, proposed the
structure, wrote the code and the tests and made the commits.

Claude Code was used as a pair programmer throughout the challenge, with the
architecture decisions recorded beforehand in a `CLAUDE.md`:

1. **Data inspection before coding:** profiling the CSVs with pandas (types, nulls,
   statuses, consistency across tables). This is what revealed the products with
   contradictory descriptions, the totals that do not match and the duplicate e-mail.
   The three decisions on these points were approved by me before any code.
2. **Folder structure proposal,** reviewed and approved before implementation.
3. **Consulting the Anthropic API reference embedded in Claude Code** (`claude-api`
   skill) before writing the tool use code, to confirm the message format and the
   details of `claude-haiku-5-5` (adaptive thinking on by default, default effort
   `medium`, response blocks returned whole to the history). The docs.claude.com site
   was not consulted directly. Later, a 400 error from the API showed that it validates
   thinking blocks against the system prompt.
4. **Implementation in stages with small commits,** with tests that do not use the API
   written alongside each module.
5. **Manual review of the outputs:** I talked to the agent through the CLI and read the
   example conversations before accepting them. This led to fixes in the code and the
   prompt: sorting results by price, opinions about a product only based on the
   description and specs, not suggesting a deadline exception and not promising a
   follow-up channel.
