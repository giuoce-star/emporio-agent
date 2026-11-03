# Promoção, PIX, parcelamento e frete

_Compra com promoção ativa: preço original + desconto, PIX que não acumula, parcelamento e frete na região metropolitana._

Modelo: `claude-sonnet-5-5` · gerado em 03/11/2026 14:17 · data de referência ("hoje"): 03/11/2026 (data real)

**Cliente:** Oi! Tô procurando um ukulele concert pra minha filha, até uns 500 reais. O que vocês têm?

> 🔧 `buscar_produtos({"termo": "ukulele concert", "categoria": "Ukuleles", "preco_max": 500, "limite": 10})`

**Empório:** Oi! Tenho boas opções de concert até R$ 500, todas disponíveis:  
  
- Kala KA-C Concert Mogno: R$ 349,90 (R$ 332,41 no PIX). Corpo em mogno maciço, acabamento acetinado.  
- Ohana CK-20 Concert Natural: em promoção, de R$ 549,00 por R$ 439,20 (20% de desconto). Tampo sólido em Spruce e fundo em Mogno. O desconto do PIX não soma com a promoção.  
- Kalani KAL-500C Concert Elétrico Natural: R$ 479,00 (R$ 455,05 no PIX). É eletroacústico, com captação piezo e pré-amplificador.  
  
A busca também trouxe o Kala KA-T Tenor Mogno (R$ 449,90), mas ele é tenor, não concert.  
  
Pra uma primeira experiência, o Kala KA-C é o mais em conta. O Ohana está com um bom desconto agora. Quer que eu veja o frete ou o parcelamento de algum deles? Pra comprar, é só chamar a equipe no WhatsApp (67) 3321-4500.

**Cliente:** Gostei do Ohana CK-20. Se eu pagar no PIX fica mais barato? E dá pra parcelar?

> 🔧 `consultar_preco({"produto_id": 121})`

**Empório:** No PIX não fica mais barato, porque o Ohana CK-20 já está em promoção. O desconto de 5% do PIX não vale sobre preço promocional, e as promoções não se acumulam. O preço é o mesmo em qualquer forma de pagamento:  
  
- Preço original: R$ 549,00  
- Promoção: 20% de desconto, por R$ 439,20  
- PIX: R$ 439,20  
- Cartão de crédito: até 5x sem juros de R$ 87,84  
  
Se quiser o menor preço, o valor promocional já é esse. Pra fechar a compra, chame a equipe no WhatsApp (67) 3321-4500. Quer que eu calcule o frete? É só me dizer a cidade.

**Cliente:** Moro aqui em Campo Grande mesmo. Quanto fica o frete?

> 🔧 `calcular_frete({"cidade": "Campo Grande", "valor_pedido": 439.2})`

**Empório:** Pra Campo Grande, o frete do Ohana CK-20 fica em R$ 35,00. A entrega leva de 1 a 3 dias úteis, por motoboy próprio da loja.  
  
O frete é grátis em pedidos acima de R$ 500,00, e o seu pedido ficaria em R$ 439,20, abaixo disso.  
  
Pra finalizar a compra, chame a equipe no WhatsApp (67) 3321-4500. Posso ajudar com mais alguma coisa?
