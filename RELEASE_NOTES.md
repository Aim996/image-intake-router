# image-intake-router 3.0.0 Release Notes

3.0.0 将产品聚焦为识图、预览与确认入口，使用 Schema `image-intake-router.v3`。每张图片先进行一次真实视觉识别；若初次结果遗漏可见关键字段，允许最多一次补充识读。清洗文字、字段证据和限制会合并为一个统一事实集。

## 用户体验

初始含图回合依次输出详细的 `【入账内容】`、`【入库内容】`、`【需要注意】`，并创建零次下游交接。用户在后续回合明确肯定确认后，OpenClaw 才发现并调用合适的下游 Skill，且同一确认最多交接一次；`只记账` 与 `只入库` 可限制范围。

隐藏、遮挡、裁切、模糊、被阻止或不可读内容会披露而不会猜测。可靠可见内容仍可使用；存在隐藏项目时，只交接可靠可见内容并保留限制说明。

## 所有权变化

路由器不再发布或拥有下游专用 adapter manifest、固定逻辑 endpoint/端口、preflight/execute/status Schema、私有 payload 映射、幂等/重试/状态协议或版本协商。OpenClaw 负责下游 Skill 发现和调用，下游 Skill 负责自己的执行、存储、恢复与兼容性。

v3 不迁移、修改或删除任何下游数据，不修改下游项目、私有 API 或数据库，也不要求下游仓库/API 变化。

## 安装与回滚

3.0.0 的精确发布资产为 `image-intake-router-3.0.0.tgz` 和 `image-intake-router-3.0.0.tgz.sha256`。按照 [安装指南](docs/INSTALL.md) 在每台设备上分别从固定 GitHub Release 下载、核验 SHA-256，并只安装归档内嵌套 Skill 目录。

保留不可变的 [v2.1.0 Release](https://github.com/Aim996/image-intake-router/releases/tag/v2.1.0)、精确旧资产 `image-intake-router-2.1.0.tgz`、`image-intake-router-2.1.0.tgz.sha256`、已验证旧 Skill 目录和旧 OpenClaw 配置。若 v3 UAT 不通过，按 [更新与回滚](docs/UPGRADING.md) 恢复这些内容；不要重命名或删除旧 tag/资产，也不要覆盖、迁移或恢复下游数据库。
