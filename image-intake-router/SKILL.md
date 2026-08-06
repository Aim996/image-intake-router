---
name: image-intake-router
description: Use when a user uploads a payment screenshot, receipt, order page, nutrition label, food package, grocery screenshot, or meal photo that may need expense and food handling.
user-invocable: true
metadata:
  openclaw:
    emoji: "📷"
    version: 2.1.0
---

# Image intake router

Use real vision once for the attachment batch. A successful or partial `recognition_run` creates one unified fact set, then two fact-only projections, one concise business preview, one later confirmation, and independent writes/recovery. Never re-read the image for either projection.

Treat `partial` as usable pixel-derived facts with disclosed crop, blur, fold, occlusion, or hidden-row limitations only when every attachment entered visual capability and every attachment status is `succeeded` or `partial`. If any attachment is `failed`, or a mixed batch contains `not_executed`, the global run is `failed`; if all attachments are `not_executed`, the global run is `not_executed`.

On the initial image turn, require a successful or partial `recognition_run`, create the fact set and preview, and make **zero business writes**. Even a confirmation word in that same message is not a confirmation. A failed or not-executed recognition run fails closed: keep fact-set quality unavailable and both projections null, explain briefly, request real visual capability or re-upload, and create no business preview, confirmation state, adapter execution, or business write.

The preview lifecycle is `draft` → `awaiting_confirmation` → `executing` → `consumed`. Only a later confirmation of the latest `awaiting_confirmation` business digest may write. Repeated confirmation of `executing` or `consumed` returns the known receipt/state with zero new writes.

Use every one-level reference directly:

- [Recognition rules](references/recognition-rules.md)
- [Calculation rules](references/calculation-rules.md)
- [Vision runtime](references/vision-runtime.md)
- [Projection contracts](references/projection-contracts.md)
- [Confirmation and execution](references/confirmation-and-execution.md)
- [Failure recovery](references/failure-recovery.md)
- [Output contract](references/output-contract.md)

Keep source facts, business meaning, adapter normalization, and public downstream payloads separate. If a required public contract cannot preserve the stated business facts, fail that domain closed rather than dropping detail or guessing. Do not persist raw images, paths, base64, full OCR, credentials, or sensitive downstream identifiers.
