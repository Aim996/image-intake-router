# Confirmation and OpenClaw handoff

The router uses only this state flow:

```text
recognizing → awaiting_confirmation → handed_off
     ├──────────── not_actionable
     └──────────── failed
```

`recognizing` is transient. A successful or partial recognition builds the latest preview and moves to `awaiting_confirmation`. A result with no executable business section becomes `not_actionable`; an unavailable or failed visual result becomes `failed`.

## Image turn

The **initial image message** performs recognition and shows the preview but creates **zero business handoffs**. Confirmation language included in the same message does not count. No downstream action is selected on the image turn.

## Later reply

Only a **later affirmative reply** to the latest preview can select content:

- `确认`, `可以`, `没问题`, `执行`, or `就这样` selects all executable sections.
- `只记账` selects accounting only.
- `只入库` selects inventory only.

Questions, clarification requests, and corrections are not confirmations. A correction must **invalidate the prior preview**, apply the correction to the canonical facts, create a new preview ID, display the replacement preview, and return to `awaiting_confirmation`.

After a valid selection, hand the confirmed content back once and enter `handed_off`. Repeated confirmation after `handed_off` creates **zero new handoffs** and only reports that the latest confirmed preview was already handed back.

**OpenClaw owns downstream Skill invocation.** The router never chooses, calls, monitors, repairs, or retries downstream Skills itself.
