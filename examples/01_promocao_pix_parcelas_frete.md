# Informações da loja, promoção, PIX, parcelamento e frete

_Informações gerais da loja (endereço e horário de sábado), compra com promoção ativa: preço original + desconto, PIX que não acumula, parcelamento e frete na região metropolitana._

Modelo: `claude-sonnet-5-5` · gerado em 03/11/2026 14:54 · data de referência ("hoje"): 03/11/2026 (data real)

**Cliente:** Oi! Onde fica a loja de vocês? E sábado abre até que horas?

**Empório:** Oi! A loja fica na Rua 14 de Maio, 3200, Centro, em Campo Grande (MS), CEP 79202-333.  
  
No sábado a gente abre das 9h às 13h. De segunda a sexta o horário é das 9h às 18h, e domingo e feriados ficam fechados.  
  
Se quiser falar com a equipe antes de passar aqui, o WhatsApp é (67) 3321-4500. Posso ajudar com mais alguma coisa, tipo ver algum instrumento?

**Cliente:** Legal! Tô procurando um ukulele concert pra minha filha, até uns 500 reais. O que vocês têm?

> 🔧 `buscar_produtos({"termo": "ukulele concert", "categoria": "Ukuleles", "preco_max": 500})`

**Empório:** Achei estas opções de concert até R$ 500, todas disponíveis:  
  
- Kala KA-C Concert Mogno: R$ 349,90 (PIX: R$ 332,41). Mogno maciço, acabamento acetinado, escala maior e confortável.  
- Ohana CK-20 Concert Natural: de R$ 549,00 por R$ 439,20 (20% de desconto). Tampo sólido em Spruce e fundo em Mogno, com tom equilibrado. O desconto da promoção não acumula com o PIX.  
- Kalani KAL-500C Concert Elétrico Natural: R$ 479,00 (PIX: R$ 455,05). É eletroacústico, com captação piezo e pré-amplificador.  
  
O Kala KA-T Tenor Mogno (R$ 449,90) também apareceu na busca, mas é tenor, não concert.  
  
Para uma criança que está começando, o Kala KA-C costuma ser uma boa escolha pelo preço. O Kalani só vale a pena se ela for tocar amplificada.  
  
Quer que eu veja o frete? Se sim, me diga a cidade. Para fechar a compra, é só chamar a equipe no WhatsApp (67) 3321-4500.

**Cliente:** Gostei do Ohana CK-20. Se eu pagar no PIX fica mais barato? E dá pra parcelar?

> 🔧 `consultar_preco({"produto_id": 121})`

**Empório:** No PIX não fica mais barato, porque o Ohana CK-20 já está em promoção. O desconto de 5% do PIX não vale sobre preço promocional, e as promoções não se acumulam. O preço é o mesmo de qualquer forma de pagamento:  
  
- De R$ 549,00 por R$ 439,20 (20% de desconto)  
- No PIX: R$ 439,20  
- No cartão de crédito: até 5x sem juros de R$ 87,84  
  
Ele tem 6 unidades em estoque. Para comprar, chame a equipe no WhatsApp (67) 3321-4500 ou venha à loja. Se quiser, também calculo o frete para a sua cidade.

**Cliente:** Moro aqui em Campo Grande mesmo. Quanto fica o frete?

> 🔧 `calcular_frete({"cidade": "Campo Grande", "valor_pedido": 439.2})`

**Empório:** Para Campo Grande, o frete do Ohana CK-20 fica em R$ 35,00. A entrega leva de 1 a 3 dias úteis, por motoboy próprio.  
  
O frete é grátis em pedidos acima de R$ 500,00. Como o ukulele sai por R$ 439,20, a taxa é cobrada.  
  
Para fechar o pedido, chame a equipe no WhatsApp (67) 3321-4500. Posso ajudar com mais alguma coisa?
