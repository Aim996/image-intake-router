# image-intake-router 2.0.1 Release Notes

2.0.0 的发布历史保持不变；本说明仅描述 2.0.1 的发布与安装。

## 安装

从 [GitHub Release v2.0.1](https://github.com/Aim996/image-intake-router/releases/tag/v2.0.1) 下载 `image-intake-router-2.0.1.tgz` 与 `image-intake-router-2.0.1.tgz.sha256`，先核验 SHA-256，再按 [安装指南](docs/INSTALL.md) 仅安装嵌套的 `image-intake-router-2.0.1/image-intake-router/` 到 OpenClaw 的 Skill 目录。安装过程不会自动替换正在运行的配置。

## 更新

升级前请完成备份并停止旧版入口。使用固定版本 2.0.1，而不是不受约束的最新版本；详细流程见 [升级与回滚](docs/UPGRADING.md)。

## 数据与迁移

本版本只提供 Skill 契约与识别路由规则，不迁移、不创建也不修改业务数据库。请保留现有数据，并在完成真实验收后再启用新 Skill。

## 已知限制

`food-image-intake` 与 `image-intake-router` 不能同时激活，避免同一图片被重复识别。没有像素的图片描述只能按用户提供的事实处理，不能声称看到了图片。

## 回滚

停用 2.0.1、恢复先前已验证版本的 Skill 目录和 OpenClaw 配置，然后执行健康检查。回滚不会修改数据库。
