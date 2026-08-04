# Failure recovery and one-time write ledger

This contract applies after a complete preview has been displayed. It does not authorize another visual pass, direct database access, a raw-image handoff, or a write before confirmation. The expense database and pantry database are separate; a result in one is never evidence of a result in the other.

## Consume before any business write

On a valid confirmation, atomically move the latest `awaiting_confirmation` revision to `executing` **before** its first business write attempt. That immediately consumes the preview's authority to execute. When all selected attempts and any required status lookups finish, move it to `consumed`, even when one or more results failed or remain indeterminate. A repeated confirmation of `executing` or `consumed` must make no new business write.

Any repair is a separate, user-visible revision containing only the still eligible uncommitted work and requires a new confirmation. It must not replay a successful expense or successful pantry item.

## Status ledger

Maintain a session-local status ledger for the selected domain and every selected pantry item. It is coordination state only: do not put raw images, paths, base64, full OCR, payment accounts, credentials, downstream identifiers, idempotency keys, or preview identifiers in the preview, note, receipt, or durable business data.

| Scope | Initial status | Legal terminal/status outcomes | Meaning and next action |
| --- | --- | --- | --- |
| `expense` domain | `not_executed` | `written`, `failed`, `indeterminate` | One prospective ledger write. |
| each `diet_projection.items[i]` | `not_executed` | `written`, `failed`, `indeterminate` | One prospective pantry write, independent of all other items. |
| excluded/uncertain pantry row | not selected | no write status | Never call the pantry writer for it. |

The status vocabulary is exact:

- `not_executed`: no write has been attempted. It may appear only before this scope/item is selected and attempted. A new revision may include it after a confirmed correction.
- `written`: the downstream tool positively confirmed the write. It is committed and must never be replayed by repeated confirmation or recovery.
- `failed`: the downstream tool positively confirmed that this write was not committed. Preserve the safe reason. It may be offered in a corrected new preview; never silently retry it from the consumed revision.
- `indeterminate`: the client cannot establish whether the downstream write committed (for example, timeout/disconnect after submission). It is neither a success nor a safe retry.

Immediately before calling its public downstream tool, change each selected entry from `not_executed` to `indeterminate`. `indeterminate` is the only four-status representation once an external call has begun: it means the result is not yet established. A definite tool success changes it to `written`; a definite non-commit failure changes it to `failed`; a timeout, crash, disconnect, or missing result leaves it `indeterminate` and enters the query-first path. Do not introduce an in-flight or any other fifth status.

## Indeterminate results: query first, never blind retry

For an `indeterminate` expense or pantry item, first use only the downstream Skill's documented status/idempotency query path (`Q`) and its public schema. Do not add parameters, edit SQLite directly, guess a lookup, or treat another confirmation as a retry request.

- If the query proves the write committed, set status to `written` and report it as committed.
- If the query proves it did not commit, set status to `failed`, state it is uncommitted, and offer a corrected preview if the user wants to retry.
- If the query is unavailable or still inconclusive, retain `indeterminate`. Report `result indeterminate; no write was repeated`, and keep it out of any automatic retry path.

Both `written` and `indeterminate` are non-replayable by repeated confirmation. The same holds when one domain succeeds while another domain fails; cross-domain rollback is prohibited.

## Independent execution and receipts

For each selected scope, call only the declared public tool payload from the projection contract. Do not call the expense writer when no executable expense exists, and do not call the pantry writer for excluded or uncertain rows. Continue reporting independently if another domain/item fails, subject to the downstream circuit-breaker contract.

Every execution receipt must explicitly enumerate both sides; never summarize partial progress as “all complete.” Use this shape, omitting only a domain that was explicitly outside the confirmation scope:

```text
Execution result (this preview is consumed)
- Expense: committed / not committed (failed) / result indeterminate; no write repeated.
- Pantry committed: <each item name>.
- Pantry not committed: <each failed item name and safe reason>.
- Pantry indeterminate: <each item name>; status checked / cannot yet be determined; no write repeated.
- Not submitted by scope: <expense or item names>.
```

`written` entries belong under committed. `failed` entries belong under not committed. `indeterminate` entries must be separately named; do not label them committed or uncommitted. `not_executed` entries must state why they were not submitted (unselected scope, non-executable projection, excluded, uncertain, or a newly required correction). This explicit accounting is also required when no tool calls occur.
