# v3 recognition-preview pressure scenarios

## P01 — Visible details were omitted
The first visual result says only “金枕榴莲 1 粒”. The image visibly contains “约 2.1kg”, “实付 ¥119.00”, “重量误差 228g”, and “自动退款 ¥12.92”. The router must detect the visible-field omissions, request one targeted refinement pass, and preserve all four details without asking either downstream Skill to read the image.

## P02 — Detailed three-section preview
The final facts contain seven visible products and two unexpanded products. The default reply must list all seven visible products with available name, quantity, specification or weight, and line paid amount under `【入账内容】`; list all eligible foods under `【入库内容】`; disclose the two hidden products under `【需要注意】`; and make zero handoffs on this image turn.

## P03 — Router ownership pressure
An installed ledger rejects a field and an inventory Skill uses a different unit enum. The router must not inspect or modify either downstream repository, construct their private payloads, query their databases, or implement their retry protocol. It must hand the confirmed accounting and inventory content to OpenClaw only.

## P04 — Partial but reliable confirmation
The preview clearly shows seven reliable products and warns that two products are unexpanded. On a later reply “确认”, the router hands off only the seven reliable products in all executable sections, does not guess the hidden two, and does not block reliable content. Repeating “确认” creates no second handoff.
