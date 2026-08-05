# image-intake-router

## 主要功能

`image-intake-router` 为支付截图、小票、订单页、营养标签、食品包装、买菜截图和餐食照片提供统一入口。同一批图片只进行一次视觉识别，生成规范化事实后同时产出随手账与食序管家的预览；只有用户确认后才允许下游写入。

## 当前稳定版本

当前稳定版本为 **2.0.1**。请从 [GitHub Release v2.0.1](https://github.com/Aim996/image-intake-router/releases/tag/v2.0.1) 下载固定版本资产。

2.0.0 保留为历史发布记录；安装与升级应使用当前固定版本 2.0.1。

## 系统要求

- 可下载 GitHub Release 资产的环境。
- 已配置的 OpenClaw 实例。
- 可单独安装 Skill 的目录，以及用于保存已验证旧版本的空间。

## 最简单的安装方法

1. 从 [GitHub Release v2.0.1](https://github.com/Aim996/image-intake-router/releases/tag/v2.0.1) 下载 `image-intake-router-2.0.1.tgz` 与 `image-intake-router-2.0.1.tgz.sha256`。
2. 核验 SHA-256 后，将发布包解压到新的 Skill 目录。
3. 在 OpenClaw 中启用 `image-intake-router`，并停用 `food-image-intake`。
4. 重载配置并按照 [安装指南](docs/INSTALL.md) 做真实验收。

## 使用示例

上传一张订单截图后，Skill 会先返回随手账和食序管家的预览。回复“确认”可执行全部可执行项；回复“只记账”或“只入库”可缩小范围。提问或修改内容不会构成确认。

## 更新方法

更新前备份当前目录与 OpenClaw 配置，下载并核验固定版本，再在新的目录安装。完整检查、健康验证与回滚步骤见 [更新与回滚指南](docs/UPGRADING.md)。

## 数据保存位置与数据安全

本仓库不保存原图、完整 OCR、支付账户、凭据或本地业务数据库。实际数据由下游系统在用户确认后处理；本版本不迁移或修改数据库结构。

## 备份与恢复

升级前保留当前已验证版本的完整 Skill 目录与 OpenClaw 配置。若新版本不符合预期，停用它并恢复该目录和配置，然后重载并进行健康检查。

## 常见问题

- **能否同时启用旧版？** 不能。`food-image-intake` 与 `image-intake-router` 同时激活会导致重复识别风险。
- **SHA-256 不一致怎么办？** 停止安装，重新从 GitHub Release 获取发布资产。
- **如何回滚？** 使用 [更新与回滚指南](docs/UPGRADING.md) 恢复已验证的固定版本和配置。

## 开发者验证

```powershell
python -m unittest tests.test_repository_contract -v
python image-intake-router\tests\test_static_contract.py -v
python -m json.tool image-intake-router\templates\image-intake-router.schema.json
```

## License

本项目采用 [MIT License](LICENSE)。
