# Confirmation and execution

## Canonical business digest

Build `business_digest` from the canonical representation of the user-confirmed business content and retain a stable fingerprint over that representation. It includes final paid amount and category business meaning; merchant and business time; every product's name, purchase count, display unit, specification, weights/volumes, line paid amount, and refund; expense/diet selected scopes and included/excluded product identities; and declared/visible/hidden counts plus the completeness warning.

The user confirms this digest, never an adapter payload. Business-field or selected-scope changes require a new preview and confirmation: amount, category, merchant, time, name, quantity, specification, line price, refund, product addition/removal, selected scope, or completeness conclusion all change the digest.

Adapter-only changes do not change the digest and do not reconfirm. They include `piece` conversion, deterministic kg/g/L/ml conversion, expiry null/omission/version adaptation, payload ordering, strict payload normalization, internal handles, adapter versions, and stable call IDs.

## Preview and confirmation

Keep `draft` → `awaiting_confirmation` → `executing` → `consumed`, with a latest-preview-only rule. The initial image turn requires a successful or partial `recognition_run`, creates one unified fact set and one business preview, and makes zero business writes. A confirmation word in that image message cannot execute; only a later valid confirmation of the latest `awaiting_confirmation` digest can execute.

Valid later confirmation may select all executable work, expense only, or diet only. Questions and clarification requests are not confirmation. When a digest business field changes, invalidate the old preview, make the new preview visible, then await its confirmation. Adapter-only corrections retain the original confirmation as described in recovery.

Before a first selected business write, atomically move the confirmed preview to `executing`; after all selected attempts and required status queries finish, move it to `consumed`. A repeated confirmation of `executing` or `consumed` returns the safe known receipt/state and makes zero new writes.

## Independent execution

Execute the selected expense scope and each eligible pantry item independently with only their public payloads. Do not run a non-executable domain. A failure in one domain or one pantry item never authorizes replay of a written expense or written sibling. The consumed preview stores safe execution outcomes for duplicate confirmations.
