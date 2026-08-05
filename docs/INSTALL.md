# 安装 image-intake-router 2.0.1

## 从 Release 获取精确资产

只从 [GitHub Release v2.0.1](https://github.com/Aim996/image-intake-router/releases/tag/v2.0.1) 下载以下自定义资产：

- `image-intake-router-2.0.1.tgz`
- `image-intake-router-2.0.1.tgz.sha256`

不要使用未固定版本的下载链接，也不要用其他文件替代校验文件。

## 先校验，再解压

### Windows PowerShell

在下载目录执行：

```powershell
Get-FileHash -Algorithm SHA256 .\image-intake-router-2.0.1.tgz
Get-Content .\image-intake-router-2.0.1.tgz.sha256
```

比较两者的 SHA-256 值；不一致时停止安装并重新下载。校验通过后解压归档，并只复制下述可安装目录到 `<OPENCLAW_SKILLS_DIR>`。

### Linux shell

在下载目录执行：

```bash
sha256sum -c image-intake-router-2.0.1.tgz.sha256
```

命令必须报告校验成功。然后解压归档，并只复制下述可安装目录到 `<OPENCLAW_SKILLS_DIR>`。

### NAS

NAS 若提供 SSH 或终端，请按 Linux shell 的 `sha256sum -c` 命令校验并解压。若只能使用 NAS GUI，请先在受信任的 Windows PowerShell 或 Linux 环境完成校验，再通过 GUI 解压和复制。无论使用 SSH/终端还是 NAS GUI，都必须保留外层包装目录的理解：只能安装嵌套的 `image-intake-router/` 目录，不能把整个归档根目录直接作为 Skill。

## 归档布局与安装目标

解压后归档布局固定如下：

```text
image-intake-router-2.0.1/
├── VERSION
├── README.md
├── LICENSE
├── CHANGELOG.md
├── docs/
└── image-intake-router/
    ├── SKILL.md
    ├── references/
    └── templates/
```

唯一可安装的 Skill 目录是 `image-intake-router-2.0.1/image-intake-router/`。将该目录放入 `<OPENCLAW_SKILLS_DIR>`，使最终路径为 `<OPENCLAW_SKILLS_DIR>/image-intake-router/`；不要安装 `image-intake-router-2.0.1/` 外层目录。

## OpenClaw 配置与真实验收

在 OpenClaw 中只启用 `image-intake-router`，并停用旧版 `food-image-intake`；二者不可同时启用。确认 `SKILL.md` 已被发现后再重载配置。发布包不会自动安装、启用或部署到真实 OpenClaw 环境。

使用一张测试图片进行真实验收：首个含图片回合只能产生预览，不能产生业务写入；确认后再检查随手账与食序管家的结果。验收完成前不要删除旧版安装目录。

## 数据与回滚边界

安装不创建、迁移或修改数据库，不覆盖用户数据或备份。保留已验证的旧 Skill 目录和 OpenClaw 配置；若验收失败，停用 2.0.1、恢复该目录和配置、重载后再进行健康检查。
