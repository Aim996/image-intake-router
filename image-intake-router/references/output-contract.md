# Output contract

## Default response

The default response is a compact business preview, not internal JSON. Use this literal section order and closing line:

```text
识别完成

【入账】
小象超市｜实付 ¥65.48
1. 甜玉米 约850g×2　¥11.78
2. 鲜牛奶 1.5L×1　¥10.90
3. 鲜牛奶 260ml×3瓶×1　¥3.00
4. 果蔬汁 300ml×1　¥0.00

【入库】
以上 4 种食品均入库。

生产日期：
鲜牛奶 1.5L｜2026-08-03
鲜牛奶 260ml×3瓶｜2026-08-02
果蔬汁 300ml｜2026-08-01

【需确认】
交易时间未显示。

回复“确认”执行；也可回复“只记账”或“只入库”。
```

The accounting section must **list every visible recognized product** that is valid for the purchase. Each line uses `display_name` and includes **name, quantity, specification or weight, and line paid amount** whenever those fields are reliable. Show the merchant and unique final paid amount once. Keep a real `¥0.00`; never describe it as free, a gift, a member benefit, or a promotion.

Inventory comes from the same product indexes. When every accounting product is an eligible received food, write **`以上 N 种食品均入库`** and do not duplicate the accounting list. When only some products qualify, list only their concise names and necessary specifications. List production dates separately only for products with a reliable visible `production_date`; include a specification when two products share a display name. **Omit the entire production-date block** when no production date is visible.

`【需确认】` contains only an **actionable** user decision: missing true transaction time, hidden products, an unreadable name/quantity/specification/actual paid amount/production date, or an uncertain validity decision. Omit the section when there is no actionable issue. Do not put refund details, short-weight details, original/unit prices, discounts, member savings, fee breakdowns, zero-price speculation, reverse calculations, interface descriptions, schema keys, preview IDs, pass counts, tool names, or internal states in the default response.

If accounting or inventory has no content, keep its section and show one concise business reason instead of an empty object. A fully refunded, cancelled, unavailable, or not-received row may be summarized as “未计入” only when the user needs that decision; do not expose the refund amount. A partial refund does not remove a received item.

For a failed visual run, do not fabricate this preview or ask for confirmation. Give a concise failure explanation and request usable visual capability or a re-upload.

## Default redaction

Default output hides evidence enums, schema keys, preview IDs, pass counts, tool names, and internal states. It also hides raw images, paths, URLs, base64, full OCR, credentials, payment accounts, and sensitive identifiers. `full_name` stays available only in bounded canonical facts for evidence and deduplication; user and downstream content use `display_name`.
