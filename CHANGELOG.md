# Changelog

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
