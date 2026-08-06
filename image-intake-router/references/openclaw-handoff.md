# OpenClaw handoff contract

The router prepares confirmed business content for OpenClaw; OpenClaw chooses and invokes installed downstream Skills.

## Content derived from one fact set

- Accounting content comes from order facts plus every visible purchased product detail, including name, quantity, specification or weight, line paid amount, refund, weight variance, and status when present.
- Inventory content includes only visible, reliable food products whose facts show they were purchased and received. Preserve the visible name, quantity, specification, weight or volume, and production date when known.
- Warnings explain every hidden or uncertain product and every excluded, cancelled, refunded, or not-received row. Never invent hidden rows or silently drop a visible row.
- Both business sections are built from the same cleaned text and canonical structured facts. Neither section may reread the image.

## Singular session handoff

The session handoff metadata contains only:

- `preview_id`: the identifier of the preview the user confirmed;
- `selected_scopes`: the confirmed subset of `accounting` and `inventory`.

OpenClaw receives the cleaned text and structured facts associated with that preview together with the selected business content. It then chooses the installed downstream Skills. The router does not choose or name a downstream tool, normalize downstream parameters, define an endpoint or port, issue a retry or status query, access a database or private API, or own an adapter lifecycle.

One later confirmation creates one handoff record for the confirmed preview. The image turn and repeated confirmations after handoff create none.
