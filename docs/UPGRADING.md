# 更新与回滚 image-intake-router 3.1.0

## 安全更新

1. 记录当前版本并备份 OpenClaw 配置。把已验证旧 Skill 保存在扫描根目录之外，同时保留固定 v3.0.0 与 v2.1.0 Release、archive 和 checksum。
2. 在每台设备上分别复制执行 [安装指南](INSTALL.md) 中对应系统的固定 GitHub Release 命令，下载 `image-intake-router-3.1.0.tgz` 与校验文件，验证 SHA-256，再安装嵌套 Skill 目录。不要用 `main`、`latest` 或未经校验的地址替代固定资产。
3. 配置真实图片能力和 `tools.media.image.attachments.mode: "all"`，确保 `maxAttachments` 覆盖实际图片数量；不要在 `tools.media.models[]` 内联 API key。
4. 只启用 `image-intake-router`，停用会造成重复识图的旧入口，重载 OpenClaw 后完成完整业务级 UAT。

更新成功必须由 UAT 证明：每张图片一次初次视觉识别、最多一次遗漏驱动的补充识读、简化商品名、真实实付、生产日期、紧凑三段预览、图片回合零交接、后续一次确认、`只记账` / `只入库` 范围，以及隐藏内容披露但可靠可见内容仍可用。

从源码维护克隆时，可在每台设备使用 `git clone https://github.com/Aim996/image-intake-router.git` 获取仓库；已有克隆先切到 `main`，再使用 `git pull --ff-only origin main` 获取公开更新。正式安装仍应切到并验证固定 `v3.1.0` tag，或优先使用已核验 SHA-256 的 Release 资产，不直接把移动分支当成发布版本。

## 回滚到 v3.0.0

若 3.1.0 UAT 不通过，优先停用并移走未通过验收的 Skill，重新从固定 [v3.0.0 Release](https://github.com/Aim996/image-intake-router/releases/tag/v3.0.0) 下载 `image-intake-router-3.0.0.tgz` 和 `image-intake-router-3.0.0.tgz.sha256`，核验哈希后恢复嵌套 Skill 与先前 OpenClaw 配置。

## 回滚到 v2.1.0

若 UAT 不通过：停用 3.1.0；移走未通过验收的 Skill 目录；恢复此前保留的 v2.1.0 Skill 目录和 OpenClaw 配置；重载并重复旧版健康检查。也可以重新从固定 v2.1.0 Release 下载 `image-intake-router-2.1.0.tgz` 与 `image-intake-router-2.1.0.tgz.sha256`，先校验哈希再恢复嵌套 Skill。

回滚只恢复 Skill 与 OpenClaw 配置。v3 本身不迁移、修改或删除下游数据，回滚也不得覆盖随手账、食序管家或任何其他下游数据库。旧 tag、资产名和 checksum 资产必须保持不变。
