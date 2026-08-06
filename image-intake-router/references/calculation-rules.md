# Canonical fact calculation rules

Calculations may only enrich the canonical fact set. Derive a value from confirmed `visible_label` or `user_text` inputs, mark it `calculated: true`, retain every input and unit as evidence, and never overwrite a visible or user-provided value. If an input is unreadable, cropped, conflicting, or unit-incompatible, keep the result unknown.

## Quantity, packaging, and nutrition

Keep purchase count, display specification, nominal weight or volume, actual weight or volume, and billing weight as separate facts. Only calculate totals when every factor and unit is explicit. Exact deterministic conversions are permitted between kg and g and between L and ml; do not cross mass and volume without an explicit density.

These examples are invariant:

```text
6 × 330ml = 1980ml
1650g ÷ 30枚 = 55g/枚
实际摄入营养 = 标签营养 × 实际摄入量 ÷ 标签基准量
```

The first result is not rounded to 2000ml. The second is a calculated average while the original total weight and count remain visible facts. The nutrition formula requires an explicit serving basis and an actual intake amount with compatible units; never assume the whole package was consumed. NRV% is not nutrient content, kJ is not kcal, and mg is not g. Missing label values remain unknown rather than becoming zero.

## Dates and amounts

`production_date` is never calculated. Record it only when the image visibly and unambiguously labels the value as a production date. Delivery time, transaction time, packaging date, best-before date, expiration date, and shelf life cannot substitute for it.

Only an amount directly paired with a unique final-payment label such as `实付` or `支付金额` can establish `final_paid_amount`. A product `line_paid_amount` must be directly paired with that product row. Keep a visibly paid `0.00` as the actual result without calling it free or a gift. Goods subtotal, discounts, coupons, fees, delivery, original/unit prices, refunds, member savings, and promotional explanations do not enter v3.1 canonical facts or business content. Never net a refund against final payment, reverse-calculate an offer, or use line totals to invent missing order structure.

Visible-count arithmetic may derive `hidden_item_kind_count` from an explicit declared count and a complete count of visible recognized rows. For example, declared 9 and visible 7 yields hidden 2 and incomplete content. Do not create placeholder rows for the two hidden products.
