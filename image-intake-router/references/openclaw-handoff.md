# OpenClaw handoff contract

The router prepares confirmed business content for OpenClaw; OpenClaw chooses and invokes installed downstream Skills.

## Content derived from one fact set

- Accounting content carries the merchant, true transaction time when known, unique final paid amount, and every valid visible product's `display_name`, quantity, specification or weight, and line paid amount.
- Inventory content includes only visible, reliable food products whose facts show they were purchased and received. Preserve `display_name`, quantity, specification, weight or volume, and reliable visible production date when known.
- Refund/cancellation text is transient classification input. A partially refunded received product remains eligible; a fully refunded, cancelled, unavailable, or not-received product is excluded. Refund amounts, weight variance, original/unit prices, discounts, fee breakdowns, member benefits, and free/gift/promotion explanations are never handed off.
- Warnings explain each actionable hidden, uncertain, or excluded product decision in business language. Never invent hidden rows or silently drop a reliable visible row.
- Both business sections are built from the same cleaned text and canonical structured facts. Neither section may reread the image.

## Singular session handoff

The session handoff metadata contains only:

- `preview_id`: the identifier of the preview the user confirmed;
- `selected_scopes`: the confirmed subset of `accounting` and `inventory`.

OpenClaw receives the cleaned text, bounded canonical facts, and selected v3.1 business content associated with that preview. `full_name` remains internal evidence/deduplication data; accounting and inventory use `display_name`. OpenClaw then chooses the installed downstream Skills. The router does not choose or name a downstream tool, normalize downstream parameters, define an endpoint or port, issue a retry or status query, access a database or private API, edit downstream code or data, or own an adapter lifecycle.

One later confirmation creates one handoff record for the confirmed preview. The image turn and repeated confirmations after handoff create none.
