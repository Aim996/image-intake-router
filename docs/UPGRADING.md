# 更新与回滚 image-intake-router 2.1.0

## 安全更新

1. 记录当前版本，备份 OpenClaw 配置，并保留已验证的 v2.0.1 Skill 目录和 [v2.0.1 Release](https://github.com/Aim996/image-intake-router/releases/tag/v2.0.1) 资产。
2. 下载固定的 2.1.0 归档和 SHA-256 文件，按 [安装指南](INSTALL.md) 校验并安装到新的并行目录。
3. 配置真实图片能力和 `tools.media.image.attachments.mode: "all"`，确保 `maxAttachments` 覆盖你的订单图片数量；不要在 `tools.media.models[]` 内联 API key。
4. 只启用 `image-intake-router`，停用会造成重复识别的旧入口，重载后完成完整业务级 UAT。

不能因文件已复制、Skill 已发现或命令没有报错而宣布更新成功。必须证明每个附件一次真实视觉运行、失败关闭、部分图片如实披露、初始零写入和一次确认。

## 回滚

若 UAT 不通过，停用 2.1.0，恢复保留的 2.0.1 Skill 目录及配置，重载并重复健康检查。回滚不覆盖随手账或食序管家的数据库：路由器本身没有业务数据库，也不执行数据库迁移。
