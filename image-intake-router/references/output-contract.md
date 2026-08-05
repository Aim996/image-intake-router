# Output contract

## Default business output

The default preview and receipt are one or two business sentences. Before confirmation, state the recognised paid amount/category meaning, visible and hidden product/completeness summary, and what executable scopes will run after confirmation. If only one domain is executable, say the other will not run and why without blocking the executable domain. Full details only on request, omission questions, or diagnostics.

Approved concise preview example (an example, not a mandatory fixed skeleton):

> 识别到本单实付 ¥65.48，共至少 9 种商品；图片完整展示了 7 种，另外 2 种未展开。准备记账 ¥65.48，并将 7 种可见食品交给食序管家，是否确认？

Approved concise receipt example (also an example, not a mandatory fixed skeleton):

> 已记账 ¥65.48，完整保存了 7 种可见商品的名称、重量、数量和价格；食序管家成功入库 6 种，1 种因数量不明确未提交。

After confirmation, state the completed business result and any safe omission reason. A failed or not-executed `recognition_run` produces no business preview or confirmation prompt; give a short failure explanation and ask for real visual capability or a re-upload instead.

## What remains visible

Visible order detail remains in structured expense `line_items`; a note summary never deletes or truncates those rows. Refund facts remain visible as facts but do not create a refund write. Do not claim an unsubmitted item was written. A partial order preview says that only visible rows were forwarded and keeps the completeness warning.

## Default redaction

Default output must not show internal evidence enums such as `visible_label` or `user_text`, `attachment_context`, category ID `shopping`, an ISO timestamp, `expires_at`, technical `piece`, preview revision, operation/call IDs, adapter versions, or internal execution-state names. It also must not show internal handles, stable IDs, raw payload ordering, or strict-normalization details.

Details may expose only the minimum useful field/evidence/confidence/adapter/error explanation. Even diagnostics must not expose credentials, raw images, paths, base64, full OCR, payment accounts, or sensitive downstream identifiers.

## Confirmation language

Ask for confirmation only after presenting the current business digest. Map later replies exactly: `确认`/`可以`/`就这样` => all executable scopes; `只记账` => expense only; `只入库` => diet only. A question is not confirmation. A changed digest produces a new concise preview and requires a new confirmation; an adapter-only correction stays under its original confirmation according to the recovery contract.
