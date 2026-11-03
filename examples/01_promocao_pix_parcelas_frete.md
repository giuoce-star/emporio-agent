# Informações da loja, promoção, PIX, parcelamento e frete

_Informações gerais da loja (endereço e horário de sábado), compra com promoção ativa: preço original + desconto, PIX que não acumula, parcelamento e frete na região metropolitana._

Modelo: `claude-sonnet-5-5` · gerado em 03/11/2026 16:16 · data de referência ("hoje"): 03/11/2026 (data real)

**Cliente:** Oi! Onde fica a loja de vocês? E sábado abre até que horas?

**Empório:** Oi! A loja fica na Rua 14 de Maio, 3200, Centro, Campo Grande (MS), CEP 79202-333.  
  
No sábado a gente abre das 9h às 13h. De segunda a sexta, o horário é das 9h às 18h. Domingo e feriados ficam fechados.  
  
Se quiser falar com a equipe, o WhatsApp é (67) 3321-4500. Está procurando algum instrumento específico? 🎸

**Cliente:** Legal! Tô procurando um ukulele concert pra minha filha, até uns 500 reais. O que vocês têm?

> 🔧 `buscar_produtos({"termo": "ukulele concert", "categoria": "Ukuleles", "preco_max": 500})`

**Empório:** Achei estas opções de ukulele concert até R$ 500, todas disponíveis:  
  
- Kala KA-C Concert Mogno: R$ 349,90 (PIX: R$ 332,41). Corpo em mogno maciço, acabamento acetinado e escala maior para mais conforto e volume.  
- Ohana CK-20 Concert Natural: de R$ 549,00 por R$ 439,20 (20% de desconto). Tampo sólido em Spruce e fundo em Mogno, com tom equilibrado e sustain impressionante para a categoria. Como já é promoção, o desconto do PIX não soma.  
- Kalani KAL-500C Concert Elétrico Natural: R$ 479,00 (PIX: R$ 455,05). É eletroacústico, com captação piezo e pré-amplificador.  
  
Tem também o Kala KA-T Tenor Mogno por R$ 449,90 (PIX: R$ 427,41). Ele é tenor, não concert, e tem escala maior e graves mais presentes.  
  
Quer que eu veja o frete ou o parcelamento de algum deles? Para comprar, é só chamar a equipe no WhatsApp (67) 3321-4500 ou passar na loja.

**Cliente:** Gostei do Ohana CK-20. Se eu pagar no PIX fica mais barato? E dá pra parcelar?

> 🔧 `consultar_preco({"produto_id": 121})`

**Empório:** No PIX não fica mais barato nesse caso. O Ohana CK-20 já está em promoção: de R$ 549,00 por R$ 439,20 (20% de desconto). Por isso o desconto de 5% do PIX não se aplica, e o valor no PIX é os mesmos R$ 439,20.  
  
No cartão de crédito dá para parcelar em até 5x sem juros, de R$ 87,84.  
  
Quer que eu calcule o frete? Me diga a cidade de entrega. Para fechar a compra, é só chamar a equipe no WhatsApp (67) 3321-4500 ou passar na loja.

**Cliente:** Moro aqui em Campo Grande mesmo. Quanto fica o frete?

> 🔧 `calcular_frete({"cidade": "Campo Grande", "valor_pedido": 439.2})`

**Empório:** Para Campo Grande, o frete do Ohana CK-20 fica em R$ 35,00. O pedido é de R$ 439,20, abaixo dos R$ 500,00 do frete grátis. A entrega leva de 1 a 3 dias úteis, por motoboy próprio.  
  
Quer fechar a compra? Chame a equipe no WhatsApp (67) 3321-4500 ou passe na loja. Posso ajudar com mais alguma coisa?
