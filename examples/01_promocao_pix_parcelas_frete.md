# Promoção, PIX, parcelamento e frete

_Compra com promoção ativa: preço original + desconto, PIX que não acumula, parcelamento e frete na região metropolitana._

Modelo: `claude-sonnet-5-5` · gerado em 03/11/2026 13:35

**Cliente:** Oi! Tô procurando um ukulele concert pra minha filha, até uns 500 reais. O que vocês têm?

> 🔧 `buscar_produtos({"termo": "ukulele concert", "categoria": "Ukuleles", "preco_max": 500})`

**Empório:** Oi! Temos boas opções de concert até R$ 500, todas disponíveis:  
  
- Kala KA-C Concert Mogno: R$ 349,90 (R$ 332,41 no PIX). Corpo em mogno maciço, acabamento acetinado.  
- Ohana CK-20 Concert Natural: em promoção, de R$ 549,00 por R$ 439,20 (20% off). Tampo sólido em Spruce e fundo em mogno. Na promoção não tem o desconto extra do PIX.  
- Kalani KAL-500C Concert Elétrico: R$ 479,00 (R$ 455,05 no PIX). É eletroacústico, com captação piezo e pré-amplificador.  
  
Tem também o Kala KA-T, mas ele é tenor, não concert: R$ 449,90 (R$ 427,41 no PIX).  
  
Pra uma primeira experiência, o Kala KA-C é o mais em conta. Se ela vai tocar ligada em amplificador, o Kalani faz sentido. Quer que eu veja o parcelamento ou o frete de algum deles? Pra comprar, é só chamar a equipe no WhatsApp (67) 3321-4500.

**Cliente:** Gostei do Ohana CK-20. Se eu pagar no PIX fica mais barato? E dá pra parcelar?

> 🔧 `consultar_preco({"produto_id": 121})`

**Empório:** Sobre o Ohana CK-20:  
  
- PIX: não fica mais barato. O preço já está em promoção (de R$ 549,00 por R$ 439,20, 20% off), e o desconto de 5% do PIX não soma com a promoção. No PIX você paga os mesmos R$ 439,20.  
- Cartão de crédito: dá pra parcelar em até 5x sem juros de R$ 87,84.  
  
Pra fechar a compra, é só chamar a equipe no WhatsApp (67) 3321-4500. Se quiser, vejo o frete pra sua cidade.

**Cliente:** Moro aqui em Campo Grande mesmo. Quanto fica o frete?

> 🔧 `calcular_frete({"cidade": "Campo Grande", "valor_pedido": 439.2})`

**Empório:** Pra Campo Grande, o frete do Ohana CK-20 fica R$ 35,00, com entrega por motoboy próprio em 1 a 3 dias úteis. Ele sai abaixo de R$ 500,00, por isso a taxa.  
  
O frete é grátis em pedidos acima de R$ 500,00. Só que o ukulele sozinho não chega nesse valor.  
  
Pra fechar o pedido, chame a equipe no WhatsApp (67) 3321-4500. Posso ajudar em mais alguma coisa?
