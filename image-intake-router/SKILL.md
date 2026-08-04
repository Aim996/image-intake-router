---
name: image-intake-router
description: Use when a user uploads a payment screenshot, receipt, order page, nutrition label, food package, grocery screenshot, or meal photo that may need expense and food handling.
user-invocable: true
metadata:
  openclaw:
    emoji: "📷"
---

# 图片识别路由器

原始图片或图片批次只识别一次。先形成可追溯的规范化事实集合，再分别生成随手账和食序管家的投影；两个投影不得重新调用视觉识别。

默认展示记账与入库两份预览。首个含图片的回合只生成最近一次完整预览，零工具调用、零业务写入；所有写入均等待该预览的后续确认。用户可回复“确认”“可以”或“就这样”执行全部可执行部分，也可回复“只记账”或“只入库”缩小范围；提问不构成确认。字段或范围修改后必须生成新修订版预览并重新确认。

预览按 `draft`、`awaiting_confirmation`、`executing`、`consumed` 流转。只有最近一次完整且处于 `awaiting_confirmation` 的预览可接受确认；开始执行前先消费预览，重复确认 `executing` 或 `consumed` 的预览不得造成新的写入。

使用下列参考资料完成识别、计算、投影、确认、输出和故障处理：

- [识别规则](references/recognition-rules.md)
- [计算规则](references/calculation-rules.md)
- [投影契约](references/projection-contracts.md)
- [确认与执行](references/confirmation-and-execution.md)
- [输出契约](references/output-contract.md)
- [失败恢复](references/failure-recovery.md)

旧版 `food-image-intake` 保留但不能与本 Skill 同时启用。本版本不自动部署到真实 OpenClaw。

For a described image with no pixels available, use the stated facts as `user_text`, explicitly say that no `visible_label` was observed, and do not claim to have seen the image; the stated facts may still be used for this rules exercise.

For every awaiting-confirmation reply, render these exact user-visible tokens byte-for-byte, without substituting or paraphrasing any label or emoji: `💰 即将记入随手账：`, then `🥗 即将交给食序管家入库：`, then the two-line prompt `是否确认执行？` and `可以回复：确认、只记账、只入库，或者直接说明修改内容。`. In particular, `💵` or any other replacement for `💰` is forbidden. Every recognised product row and every recognised fee/service must appear exactly once as a pantry candidate, excluded item, or uncertain item; a fee remains excluded even when it is also an expense auxiliary amount.

Use this literal reply skeleton; fill in only the content between its lines:

```text
💰 即将记入随手账：

🥗 即将交给食序管家入库：

是否确认执行？
可以回复：确认、只记账、只入库，或者直接说明修改内容。
```
