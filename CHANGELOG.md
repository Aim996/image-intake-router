# Changelog

## [3.1.0] - 2026-08-07

### Added

- 为商品事实增加 `display_name`，并把可靠可见的生产日期稳定交给库存内容和确认预览。
- 增加九商品紧凑预览、相同简化名不同规格、零元实付、退款有效性和生产日期定向补识读回归样例。

### Changed

- Schema 升级为 `image-intake-router.v3.1`；默认预览改为 `【入账】`、`【入库】`、可选 `【需确认】`，商品列表只展示一次。
- 统一事实与 handoff 只保留真实最终/行实付；退款文字仅临时用于判断取消、未收到、全额退款或部分退款状态。

### Fixed

- 防止生产日期明明可见却遗漏，防止商品营销全名挤占确认页，防止用退款再次抵扣最终实付或倒推优惠。
- 防止内部单位、空字段或技术重试改变业务确认并引发重复 handoff。
- 允许真实订单最终实付为 `¥0.00`；为商品状态、类型、可见性和生产日期来源增加严格 Schema/运行时门禁，阻止无效行进入可执行内容。
- 将未版本化行为矩阵升级为 v3.1 handoff-only 契约，移除路由器直接写入、查询或修复下游参数的旧说明。

### Security

- 路由器继续不修改下游项目、私有 API、数据库或数据；3.1.0 不涉及数据库结构变化。
- 保持发布 allowlist、SHA-256、UTF-8、符号链接、重复成员、路径穿越和隔离安装门禁。

## [3.0.0] - 2026-08-06

### Added

- 聚焦真实视觉识别所有权：每张图片一次初次识读，并可在遗漏可见字段时进行最多一次补充识读。
- 以 `image-intake-router.v3` 输出清洗后的统一事实、可见字段审计及固定顺序的 `【入账内容】`、`【入库内容】`、`【需要注意】` 详细预览。

### Changed

- 初始含图回合保持零交接；用户后续肯定确认后，由 OpenClaw 发现并调用下游 Skill，且最多交接一次。
- `只记账` 和 `只入库` 可限制交接范围；隐藏或不可读内容明确披露，可靠可见内容仍可使用。

### Fixed

- 移除路由器拥有的下游专用 adapter manifest、固定 endpoint/端口、preflight/execute/status 响应、私有 payload 映射、幂等契约与版本协商文档。

### Security

- 路由器不检查或修改下游项目、私有 API、数据库或数据；v3 不迁移、修改或删除下游数据，也不要求下游仓库/API 变化。
- 保持发布 allowlist、校验和、UTF-8、符号链接、重复成员、路径穿越及隔离安装安全门禁；不涉及数据库结构变化。

## [2.1.0] - 2026-08-05

### Added

- 以一次真实像素/媒体识别生成统一详细事实，并让随手账与食序管家复用该事实。
- 随手账公开标量商品明细：名称、规格、数量、实付金额与退款事实。
- 每附件真实视觉门禁、来源/置信度/计算元数据和图片完整性披露。

### Changed

- 默认输出改为简洁业务预览；初始图片回合零业务写入，后续只需一次业务确认。
- 发布包现在包含直接链接的 `references/vision-runtime.md`，完整包含七个运行时参考文件。

### Fixed

- Corrected multi-attachment recognition aggregation so any failed attachment or mixed-batch skipped attachment fails closed with unavailable facts, null projections, no confirmation state, and zero business writes; usable cropped or folded images remain `partial`.

- 视觉失败、未执行或附件覆盖不完整时失败关闭，禁止用附件描述或文件名填充事实。
- 折叠订单如实报告可见和隐藏商品数量，不猜测未展示明细。

### Security

- 保持不存储原图、完整 OCR、凭据或本地业务数据库；幂等恢复先查询状态，禁止盲目重试。

## [2.0.1] - 2026-08-05

### Added

- 发布前严格验证源路径和归档版本，并严格解析受支持的 frontmatter。
- 提供 Windows PowerShell、Linux 和 NAS 的精确跨平台安装与验收指引。

### Changed

- 工作流发布权限已隔离，GitHub Actions 固定为不可变 action pin。
- 发布资产和可安装的嵌套 Skill 目录均使用精确名称说明。

### Fixed

- 明确归档外层包装目录与唯一可安装目录，避免将整个归档错误安装。

### Security

- 不更改协议、Schema、数据库、迁移、备份或用户数据。

## [2.0.0] - 2026-08-05

### Added

- 发布版本文件、MIT 许可证、安装说明、升级说明和可复用的 AI 提示词。
- 以 GitHub Release 为入口的公开安装与验收流程。

### Changed

- README 调整为面向发布使用者的指南，并明确数据边界与恢复步骤。
- 项目说明改为公开产品文档，不再依赖开发者机器路径。

### Fixed

- 明确旧版 `food-image-intake` 与本 Skill 不能同时启用。

### Security

- 发布包不保存原图、完整 OCR、支付账户、凭据或本地业务数据库。
- 不涉及数据库结构变化。
