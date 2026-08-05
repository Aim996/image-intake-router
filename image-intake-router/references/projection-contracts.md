# 投影契约

投影只能读取同一份规范化 `facts`，不重新读取原图。它们是确认前的预览数据，不能
携带原图、路径、base64、完整 OCR、支付账户、凭据、内部句柄或预览标识。

## `expense_projection`

费用投影是严格对象，且**只能**有以下十一个字段，顺序为：

1. `executable`：布尔值。
2. `amount`：正的人民币元数值，或 `null`。
3. `category_id`：现有随手账分类 ID，或 `null`。
4. `occurred_at`：带时区的 ISO 8601 时间，或 `null`。
5. `source_kind`：恒为 `"image"`。
6. `merchant`：商家名，或 `null`。
7. `note`：商品备注，或 `null`；最长 1000 个字符。
8. `issues`：未解决问题的字符串数组。
9. `line_items`：可见商品的 v0.3 结构化事实快照数组。
10. `detail_completeness`：`complete`、`partial` 或 `unavailable`。
11. `omitted_item_count`：未包含在 `line_items` 中、但已知存在的商品种类数。

`executable: true` 时，`amount`、`category_id` 与 `occurred_at` 必须非空。执行 `expense_entry(action="create")` 的公开参数白名单只有：必传的 `amount`、`category_id`、`occurred_at` 与恒定 `source_kind: "image"`；非空时可选的 `merchant`、`note`；以及存在时可选的 v0.3 结构化 `line_items`（1 至 100 项）。`line_items` 必须原样转发，不能静默丢弃或缩减为 `note`。不得传 `entry_type` 或任何其他字段，尤其不得传路由器内部的 `executable`、`detail_completeness`、`omitted_item_count` 或 `issues`。

`amount` 的范围必须与公开账本 Schema 一致：大于 0 且不超过 `9999999999.99`。`occurred_at`
必须是 20 到 40 个字符的带时区 ISO 8601 时间；这两个边界在基础投影和可执行分支都必须
保持一致。

`expense_projection` 同时包含路由器预览状态和下游公开账本写入 payload；其公开参数白名单以上述规则为准。`executable`、`detail_completeness`、`omitted_item_count` 和 `issues` 是路由器内部元数据，绝不作为账本参数；若已安装账本未声明 `line_items`，必须标记兼容性不满足为不可执行/错误，而不是删除明细或调用旧 payload。

一张票据或一笔订单只产生一笔费用投影，绝不按商品拆账。若存在可识别的实际购买商品，
`note` 是面向人的简短摘要，在长度允许时列出商品名称（包括非食品），但从不作为完整单品清单或价目表。只有带唯一、直接的
最终实付标签的金额可填入 `amount`；原价、小计、优惠、运费、服务费、退款或其他辅助
金额绝不能替代它。

`line_items` 保留每个可见商品的结构化业务事实，独立于最长 1000 字符、面向人的 `note`；`note` 截断或概括时不得删除 `line_items` 的可见事实。`detail_completeness: "complete"` 仅表示商品明细完整且 `omitted_item_count` 为 0；`"partial"` 表示只路由可见明细，并把已知未展开、隐藏或裁切的商品种类计入 `omitted_item_count`；`"unavailable"` 表示没有可安全路由的商品明细。`omitted_item_count` 只计数已知遗漏，未知数目不得伪造为完整。

`executable: false` 时，`amount`、`category_id`、`occurred_at`、`merchant` 与 `note`
均为 `null`，并且 `issues` 至少包含一个面向人的不执行原因。`source_kind` 仍是
`"image"`，但不得调用账本写入工具。

## `diet_projection`

饮食投影是严格对象，必有 `items`、`item_audit`、`excluded_items` 与 `uncertain_items` 四个数组。
空数组是有效结果；没有 `items` 即没有可提交的入库写入。

`business_products` 保留统一的业务商品事实，`adapter_payload` 则是独立的技术归一化输入；两者都不替换原始 `facts`，也不替换传给下游公开工具的 `items` 写入 payload。

`items` 的每个元素就是一个严格的 `diet_pantry(action="add")` 公开参数对象，而不是
路由器私有的中间格式。它只可使用下列、已经由下游公开 Schema 声明的字段：

- 必填：`action: "add"`、`food_name`、`quantity`、`unit`、`source_text`。
- 可选名称与包装字段：`normalized_name`、`package_count`、`quantity_per_package`、
  `package_unit`、`display_quantity`、`display_unit`、`base_quantity_per_display_unit`、
  `package_hierarchy`。
- 可选标签营养：`nutrition_profile`，其字段按公开 Schema 为 `normalized_name`、可选
  `brand`/`product_key`、`serving_basis`、`nutrition`、`source_text` 和 `source_grade`。
- 到期信息（二选一且互斥）：`expiry_date` 是公开 Schema 的 `date` 格式；或 `expires_at`
  是公开 Schema 接受的字符串或 `null`。图片没有可靠日期时必须传 `expires_at: null`，绝不
  编造日期。

包装三元组 `package_count`、`quantity_per_package`、`package_unit` 必须同时出现；显示包装
三元组 `display_quantity`、`display_unit`、`base_quantity_per_display_unit` 也必须同时出现。
这既保留包装数与每包装量，也不伪造换算。`source_text` 是下游已声明的简短人类来源摘要：
必须是一行、1 至 240 个字符，不能是完整 OCR，也不能含账号、凭据、原图、路径或 base64。
它不是唯一审计载体。

只有可靠识别、确实已购买并实际收到的食品可出现在 `items`。非食品、费用、广告、取消、
退款、缺货、未送达项目必须不在其中。为遵守下游公开工具契约，不能另加 `status`、
`evidence`、`item_price` 或任何路由器私有字段；状态与证据不写入下游 add payload。
订单总额绝不写入 `price`、`price_minor`、`currency` 或任何单品价格字段，除非图片对该
单品明确给出价格；本版本的投影因此不输出这些价格字段。

`item_audit` 是严格的路由器预览审计数组，**永不**传给 `diet_pantry add`。每项必须含
`item_index`、`order_status` 和至少一条结构化 `evidenceRecord`；`order_status` 只能是
`purchased_and_received`，表示该食品既已购买又已实际收到。线下已完成购买或已完成配送的
食品，在证据充分时可归一为 `purchased_and_received`；未送达、仅下单或仅付款都不构成该
状态，必须进入 `uncertain_items`，不得进入 `items` 或 `item_audit`。它与 `items` 长度相等，
索引从 0 开始、覆盖每个 `items` 元素且不得重复。执行器只提交 `items[item_index]`，并在写入
前检查这项平行关系。

`excluded_items` 与 `uncertain_items` 的每项都有 `item_name`、`status`、`reason` 和
`evidence`。`reason` 必须是人类可读的排除或不确定原因；这些数组只用于预览解释，绝不
传给 `diet_pantry add`。

## 事实与质量门槛

任何已知的文本、金额或数量事实必须至少附带一条 `evidenceRecord`；未知值使用 `null` 时
才允许空证据。每个商品行事实同样必须至少有一条证据。`quality.fact_set_status: "complete"`
只允许在 `facts.unresolved_issues` 和 `quality.issues` 都为空、且所有已知事实满足证据门槛时
使用。
# Positive order-expense recipe

When one order has one unique, directly labelled final-paid amount and its ordinary order facts are otherwise usable, build an executable expense projection. For a mixed supermarket order, the real public mapping is exactly `category_id: "shopping"`; if that ID is unavailable in the public ledger contract, mark the projection non-executable rather than guessing or using a display name. If the image has no reliable transaction time, use the current session time with its timezone as `occurred_at`. `merchant` remains `null` when unknown. Therefore a missing merchant or image timestamp alone is not a reason to suppress the expense projection. Mark it non-executable only when the paid amount is missing/conflicting, `shopping` is unavailable, or another stated execution requirement is genuinely unresolved.
