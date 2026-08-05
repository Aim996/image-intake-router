# 安装 image-intake-router

## 系统要求

- 可访问 GitHub Release 的环境。
- 已安装并可重载 OpenClaw。
- 一个独立的 Skill 安装目录；不要覆盖未备份的现有目录。

## 从 GitHub Release 安装

1. 下载固定版本 `image-intake-router` 2.0.0 的发布包及其 SHA-256 值。
2. 在本地计算下载包的 SHA-256，并与 GitHub Release 中的值逐字比对；不一致时停止安装并重新下载。
3. 解压到新的 Skill 目录，保留原有 Skill 目录以便回滚。
4. 停用旧版 `food-image-intake`，不要与 `image-intake-router` 同时启用。

## OpenClaw 配置与重载

在 OpenClaw 中只启用 `image-intake-router`，确认其 `SKILL.md` 已被发现后再重载配置。发布包不会自动安装、启用或部署到真实 OpenClaw 环境。

## 真实验收

使用一张测试图片进行真实验收：首个含图片回合只能产生预览，不能产生业务写入；确认后再检查随手账与食序管家的结果。验收完成前不要删除旧版安装目录。

## 常见错误

- SHA-256 不一致：停止使用该下载包，重新取得发布资产。
- 两个入口同时触发：停用 `food-image-intake` 或 `image-intake-router` 其中之一。
- 重载后未发现 Skill：检查解压层级和 OpenClaw 的 Skill 搜索目录，不要通过覆盖其他项目来解决。
