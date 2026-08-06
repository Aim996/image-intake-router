# 计算规则

本规则只从已确认的 `visible_label` 或 `user_text` 事实导出 `calculated` 事实。原始标签值、用户补充值和计算值必须分开保留，并保留输入与单位；看不清、被截断或单位不一致时不计算。

## 包装与营养不变量

只允许在明确的包装数量、净含量、件数或标签基准之间计算。`g` 只与 `g` 计算，`ml` 只与 `ml` 计算；未提供密度时不得跨单位换算。标称“约重”不当作实重，整包净含量也不自动等于实际摄入量。

以下三条公式为固定不变量：

```text
6 × 330ml = 1980ml
1650g ÷ 30枚 = 55g/枚
实际摄入营养 = 标签营养 × 实际摄入量 ÷ 标签基准量
```

第一条的总容量不得为了好看取整为 2000ml。第二条得到的是计算的平均单件重量，1650g 总重和 30 枚件数仍分别保留。第三条只在标签基准和实际摄入量明确且单位相容时使用；每 100g 只配 g，每 100ml 只配 ml。用户未提供实际摄入量时，不把整包默认视为已摄入；标签只供查看时也不强制追问摄入量。

营养表中的 NRV% 不参与含量计算，kJ 不与 kcal 混同，mg 不与 g 混同。标签未标注的营养字段记为“未标示”，不得以 0 补齐。日期只在生产/起算日期和保质期都明确时才可推算到期日，模糊日期保留原文。

## 金额边界

只有带有唯一、直接对应的最终付款标签（如“实付”或“支付金额”）的金额，才能成为订单的 `final_paid_amount`，并可被后续费用投影视为消费金额。若存在多个候选金额、标签不完整、订单身份不明或金额冲突，则 `final_paid_amount` 为未知，并在未解决问题中说明。

每个可见金额必须写入对应的独立订单事实：商品小计为 `goods_subtotal`，活动优惠为 `activity_discount`，券类优惠或红包为 `coupon_discount`，包装/服务费为 `packaging_fee`，配送费为 `delivery_fee`，退款总额为 `refund_total`。这些字段、商品行的 `original_amount`/`unit_price`/`line_paid_amount`/`refund_amount` 都不能替代唯一可信的 `final_paid_amount`。退款只记录可见事实和状态；本任务不实现退款记账、净额抵扣或任何账目写入。

## v2.1 unified-fact calculation boundaries

- Preserve purchase count separately from nominal, actual, and billing weight or volume. Preserve the visible display specification and display quantity unit alongside every normalized numeric measurement; an unknown value is `null`, never a synthetic zero or empty string.
- Any derived value is marked `calculated: true` and carries evidence for every input. Convert L to ml and kg to g only with the exact deterministic scale (1 L = 1000 ml; 1 kg = 1000 g). Do not infer an actual corrected weight merely from a short-weight variance.
- Refunds remain independent visible facts. Do not net a refund against final paid amount unless the image explicitly defines that relationship.
- If seven item kinds are visible and two remain hidden, record declared 9, recognized 7, hidden 2, and incomplete content. Do not manufacture hidden-product placeholder rows.
- Technical adapters may normalize to `g`, `ml`, or `piece`, but they consume the unified business facts and never trigger a second visual read.
