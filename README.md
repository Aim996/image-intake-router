# image-intake-router 2.0.0

面向 OpenClaw 的统一图片识别与双路由 Skill。对同一批图片只进行一次视觉识别，形成统一事实后，默认同时生成随手账和食序管家两份预览；只有用户明确确认后，才允许下游执行写入。

## 工作流

```text
图片批次只识别一次
        ↓
统一事实、跨图去重
商品名、数量、规格、实付金额、商家、时间、订单状态
        ↓
默认展示两份预览
        ├─ 随手账 expense_projection
        └─ 食序管家 diet_projection
        ↓
确认 / 只记账 / 只入库 / 修改内容
        ↓
确认后一次性执行
```

## 核心约束

- 第一轮图片处理只展示预览，业务写入次数必须为零。
- 一张订单或票据只生成一笔账目，备注列出可识别的实际购买商品名称。
- 只有具备 `purchased_and_received` 证据的食品才能进入食序管家入库候选。
- 修改预览会生成新 revision；旧 revision 立即失效。
- 执行前先消费预览，重复确认不会产生新的业务写入。
- 部分失败或结果不确定时先查询状态，不盲目重试成功域。
- 不保存原图、完整 OCR、支付账户、凭据或本地业务数据库。

## 目录

- `image-intake-router/SKILL.md`：Skill 入口与路由总规则。
- `image-intake-router/references/`：识别、计算、投影、确认、输出和失败恢复规则。
- `image-intake-router/templates/`：严格 JSON Schema。
- `image-intake-router/tests/`：静态契约和行为用例。
- `项目说明.md`：产品说明与安装边界。
- `约束文档.md`：隐私、执行和兼容性约束。
- `后续迭代计划.md`：后续版本规划。

## 验证

```powershell
python image-intake-router\tests\test_static_contract.py -v
python -m json.tool image-intake-router\templates\image-intake-router.schema.json
```

当前版本的静态契约包含 12 项检查。发布仓库不会自动安装或启用正在运行的 OpenClaw 配置。
