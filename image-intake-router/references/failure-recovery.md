# Failure recovery and one-confirmation write ledger

Maintain a session-local ledger for the selected expense operation and each selected pantry item. Use stable operation IDs internally; never expose them by default. Do not directly edit SQLite, add undocumented parameters, or treat a repeated confirmation as a new write request.

Execution statuses are exactly: `not_executed`, `written`, `failed_before_write`, `indeterminate`.

| State | Meaning | Required action |
| --- | --- | --- |
| `not_executed` | No downstream submission has begun. | It can be selected for the confirmed operation. |
| `written` | The downstream positively committed. | Never replay it. |
| `failed_before_write` | The downstream/schema positively proves no commit. | It may have one deterministic adapter-only correction. |
| `indeterminate` | Submission may have happened, but commitment is unknown. | Query documented status/idempotency state first. |

There is no generic terminal `failed` state in the execution ledger. Immediately before a public call, record `indeterminate`; definite success becomes `written`, and positive proof that no write committed becomes `failed_before_write`.

## One deterministic correction

Permit at most one deterministic adapter-only correction after a definite pre-write failure, only when the business digest is unchanged. Examples include converting `piece`, deterministic kg→g or L→ml conversion, and omitting a rejected null expiry when the installed public schema documents that adaptation. This correction stays under the original one confirmation, does not replay the expense or any written pantry item, and does not ask for a second confirmation.

If a repair changes amount, identity, quantity business meaning, specification, price, refund, selected scope, or completeness, it is a business change: stop, create a new preview, and require a new confirmation.

## Indeterminate results

For `indeterminate`, queries the documented downstream status/idempotency state first. Never resubmit blindly. If that query proves commitment, change to `written`; if it positively proves no commitment, change to `failed_before_write`; otherwise retain `indeterminate`, report the uncertainty safely, and make no automatic retry.

## Independent outcomes and receipt

Expense success followed by pantry failure or correction never replays the expense. One pantry item failure does not replay written siblings; continue independent eligible items unless a downstream circuit breaker requires stopping that domain. The consumed receipt records committed, failed-before-write, indeterminate, and not-submitted outcomes without calling them internal states in the default user output.
