# Output contract

## Default response

The default response is a detailed business preview, not internal JSON. Use this literal section order and closing line:

```text
识别完成

【入账内容】
商家：某某超市
时间：2026-08-06 18:30
实付：¥65.48
1. 甜玉米，约850g × 2，实付 ¥11.78
2. 鲜牛奶，1.5L × 1，实付 ¥10.90

【入库内容】
1. 甜玉米，约850g × 2
2. 鲜牛奶，1.5L × 1

【需要注意】
页面显示另有 2 种商品未展开，本次未识别、未猜测、不会提交。

请核实以上内容，回复“确认”后执行。
```

The preview must **list every visible recognized product**. In accounting, product lines include **name, quantity, specification or weight, and line paid amount** whenever those fields are visible. Compact punctuation is allowed, but no visible row may be dropped. Show merchant, transaction time, final paid amount, refunds, weight variance, status, and other useful order or product details when they are visibly available.

Inventory lists every visible product eligible under the inventory rules. `【需要注意】` explains hidden rows, unreadable or uncertain fields, excluded products, cancelled or refunded rows, and not-received products. If accounting or inventory has no content, keep the section and show a concise business reason instead of an empty object.

For a failed visual run, do not fabricate this preview or ask for confirmation. Give a concise failure explanation and request usable visual capability or a re-upload.

## Default redaction

Default output hides evidence enums, schema keys, preview IDs, pass counts, tool names, and internal states. It also hides raw images, paths, URLs, base64, full OCR, credentials, payment accounts, and sensitive identifiers. The default response stays in business language even though the handoff retains cleaned text and structured facts.
