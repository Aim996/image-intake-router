# 输出契约

每个等待确认的最近一次完整预览必须按以下顺序输出，先展示双预览，再展示确认提示。预览阶段不调用业务写入工具。

💰 即将记入随手账：

仅展示存在的投影字段。若费用域有可执行投影，展示其可见摘要；若费用域无可执行投影，仍必须显示明确的不执行原因（例如“未识别到可信实付金额，本次不执行记账”），且不调用该域写工具。

🥗 即将交给食序管家入库：

仅展示存在的投影字段。若饮食域有可执行投影，展示其可见摘要；若饮食域无可执行投影，仍必须显示明确的不执行原因，且不调用该域写工具。

是否确认执行？
可以回复：确认、只记账、只入库，或者直接说明修改内容。

用户提出问题时，回答问题或澄清预览，但不把该消息当作确认；用户说明修改内容时，生成新的完整双预览修订版，而非执行旧预览。
## Structured preview rendering

Natural-language previews may describe a value as unknown or explain that the
current zoned session time will be selected at preview creation. If the reply
also shows a JSON object representing the router preview, that object is a
real structured representation and must validate against
`templates/image-intake-router.schema.json`; do not show schema-shaped
pseudocode as JSON.

In particular, every `evidenceRecord` has exactly the declared fields:
required `source` and `value`, with optional `location` and `reason`. Do not
substitute an undeclared `text` field. An `occurred_at` included in JSON must
be the actual generated ISO 8601 timestamp with a timezone; a placeholder such
as `<current-session-time-with-+08:00>` is not valid JSON contract data. If an
actual legal value is not available for display, omit the structured JSON and
give the timing explanation in natural language instead.

For a complete diet preview, enumerate every recognised non-food item and
every recognised fee/service as a distinct `excluded_items` entry. In
particular, a delivery fee remains an expense auxiliary amount and must also
appear as an excluded diet item; do not silently omit it merely because it is
not a purchasable product.

The awaiting-confirmation user-visible labels are exact contract text, not
styling suggestions. Render exactly `💰 即将记入随手账：` followed by
`🥗 即将交给食序管家入库：`, and end with these exact two lines:

```text
是否确认执行？
可以回复：确认、只记账、只入库，或者直接说明修改内容。
```

For every recognised product row and every recognised fee/service, show one
and only one routing disposition: a pantry candidate, an excluded item, or an
uncertain item. This visibility rule applies even when the same fee also
appears as an expense auxiliary amount.

For a described-image rules exercise whose expense projection is executable,
the human-visible expense preview must show the real public category mapping
including `shopping`, the actual generated ISO 8601 `occurred_at` with
timezone, and that merchant is not provided. The human-visible diet preview
must separately enumerate every suggested, excluded, and uncertain item. A
JSON router preview is optional; if shown, it must validate against the strict
template above, use `merchant: null` for an unknown merchant, and use an
actual zoned `occurred_at`, never a city label or placeholder. This does not
permit raw image data, full OCR, credentials, or internal identifiers.

The expense note lists recognised purchased product names only. Do not append
delivery fees, service fees, discounts, refunds, or other auxiliary amounts to
that note; list those separately as their own visible auxiliary facts and diet
exclusions.
