\# Projeto: agente de atendimento da Empório da Música (desafio técnico AI Engineer, Artefact)



\## Objetivo

Agente de mensagens de texto em Python para uma loja fictícia de instrumentos

musicais (Campo Grande/MS). Persona alinhada à loja, consulta a dados (CSVs em

data/), consulta a políticas (data/politicas\_da\_loja.pdf) e trata perguntas fora

de escopo. A avaliação foca em raciocínio e decisões justificadas, não em

solução perfeita.



\## Prazo

Entrega hoje às 23h (fuso a confirmar). Prioridade: versão mínima funcionando

de ponta a ponta primeiro, melhorias depois. Último push às 22h.



\## Arquitetura (decidida)

\- Agente com function calling (tool use nativo), sem LangChain/LangGraph.

&#x20; Loop simples: mensagem -> LLM -> tool calls -> resultados -> resposta.

\- Tools de dados (pandas, determinísticas): buscar\_produtos, consultar\_preco

&#x20; (promoção e desconto PIX calculados em código, nunca pelo LLM),

&#x20; status\_pedido (com verificação mínima de identidade).

\- Políticas: o PDF é curto; extrair o texto e injetar inteiro no prompt de

&#x20; sistema (sem RAG). Justificar no README: cabe no contexto e RAG adicionaria

&#x20; complexidade sem ganho de precisão.

\- Chamada ao modelo isolada em um único arquivo (llm.py), para trocar de

&#x20; provedor com pouco custo.

\- Persistência: histórico em memória + arquivo JSON por sessão.

\- Interface: CLI.

\- Reclamação: resposta padronizada, sem tool.



\## Provedor e modelo

\- Provedor: Anthropic, SDK Python oficial `anthropic`.

\- Modelo configurável pela variável MODEL. Padrão: claude-haiku-5-5

&#x20; (desenvolvimento e testes). claude-sonnet-5-5 só na validação final dos

&#x20; cenários difíceis e nas conversas de exemplo.

\- Orçamento da API: US$ 5. Testes das tools de dados e do cálculo de preço não

&#x20; devem chamar a API. Nunca rodar loops de teste que chamem o modelo.

\- Chave em ANTHROPIC\_API\_KEY, lida de .env (python-dotenv). Criar .env.example

&#x20; sem chave real e colocar .env no .gitignore ANTES do primeiro commit. Nunca

&#x20; commitar chave.

\- Antes de escrever o código de tool use, consultar a documentação atual em

&#x20; docs.claude.com para confirmar nomes de parâmetros e formato de mensagens, em

&#x20; vez de assumir de memória.



\## Regras de negócio críticas (do PDF)

\- A loja vende SÓ instrumentos. Acessórios (cordas, palhetas, cabos, cases,

&#x20; pedais, amplificadores): redirecionar com educação.

\- Nunca informar preço, estoque ou prazo sem consultar o sistema.

\- Desconto PIX (5%) NÃO vale sobre preço já promocional. Promoções não são

&#x20; cumulativas.

\- Preço promocional sempre exibido com preço original e percentual de desconto.

\- Promoção expirada: informar com transparência e apresentar o preço atual.

\- Frete na região metropolitana de Campo Grande: grátis acima de R$ 500, senão

&#x20; R$ 35. Outras cidades: cotação por CEP (o agente não calcula).

\- Devolução por arrependimento: 7 dias corridos. Troca por defeito: 30 dias.

&#x20; Garantia legal: 90 dias. Separar os três com clareza no prompt.

\- Reclamação: empatia, registrar, retorno em 24 horas úteis.

\- Tom: informal mas profissional, como um amigo que entende de música.

\- O manual é interno: o agente aplica as regras, não cita nem expõe o documento.

\- O catálogo do CSV (65 itens) é menor que os "300+" do manual: falar só do que

&#x20; está no sistema.



\## Inconsistências do PDF (assumir e documentar no README)

\- Telefone da loja (67) 3341-4444 vs WhatsApp (67) 3321-4500: usar cada um no

&#x20; seu contexto.

\- E-mail com e sem acento: assumir contato@emporiodamusica.com.br.

\- Parcelamento: tabela diz mínimo R$ 100 para 12x, e a seção 3.1 detalha faixas

&#x20; (R$ 80 para 4x a 6x): assumir a seção 3.1.



\## Processo

\- Commits pequenos e frequentes com mensagens claras (histórico real é exigido,

&#x20; sem force-push).

\- Inspecionar os CSVs antes de codar: tratar preços, acentos, status, nulos,

&#x20; normalização para busca (ex.: "Takamine GD20").

\- Testes simples das tools de preço e de busca (sem chamar a API).

\- Entregar 3 a 5 conversas de exemplo em examples/ (ao menos uma não trivial:

&#x20; devolução com regras do manual, ou preço com promoção).

\- README rascunhado ao longo do trabalho: instruções, justificativa das

&#x20; decisões, limitações, suposições, e uso do Claude Code (registrar como foi

&#x20; usado). Atualizar uma seção a cada etapa concluída.



