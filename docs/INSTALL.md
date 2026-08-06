# 安装 image-intake-router 3.1.0

## 准备真实图片能力

在 OpenClaw 中配置支持图片的原生模型，或配置 `tools.media` 图片提供方。不要把 API key 直接写进 `tools.media.models[]`，应使用正常的 provider/auth 配置。

OpenClaw 的媒体附件策略可能默认只处理第一个附件。多张图片必须设置 `tools.media.image.attachments.mode: "all"`，并给出足够大的 `maxAttachments`：

```json5
{
  tools: {
    media: {
      image: {
        enabled: true,
        attachments: { mode: "all", maxAttachments: 10 },
      },
    },
  },
}
```

3.1.0 使用 Schema `image-intake-router.v3.1`。每张图片先完成一次初次真实视觉识别；仅在初次结果遗漏可见关键字段时，允许最多一次补充识读。文件名、描述或用户转述不能替代看图。参阅 OpenClaw 官方 [media-understanding](https://github.com/openclaw/openclaw/blob/main/docs/nodes/media-understanding.md) 与 [media overview](https://docs.openclaw.ai/tools/media-overview)。

## 获取并校验固定资产

每台设备都只从固定 GitHub Release `v3.1.0` 下载 `image-intake-router-3.1.0.tgz` 和 `image-intake-router-3.1.0.tgz.sha256`。下列命令会下载、核验并安装归档内真正的 Skill 目录。`--global` 供本机所有 OpenClaw agent 使用；只安装到当前 workspace 时去掉它。

### Windows PowerShell

```powershell
$ErrorActionPreference = "Stop"
$workDir = Join-Path $env:TEMP ("image-intake-router-3.1.0-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $workDir | Out-Null
$archive = Join-Path $workDir "image-intake-router-3.1.0.tgz"
$checksum = "$archive.sha256"
Invoke-WebRequest -Uri "https://github.com/Aim996/image-intake-router/releases/download/v3.1.0/image-intake-router-3.1.0.tgz" -OutFile $archive
Invoke-WebRequest -Uri "https://github.com/Aim996/image-intake-router/releases/download/v3.1.0/image-intake-router-3.1.0.tgz.sha256" -OutFile $checksum
$expected = ((Get-Content -LiteralPath $checksum -Raw).Trim() -split "\s+")[0].ToLowerInvariant()
$actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash.ToLowerInvariant()
if ($actual -ne $expected) { throw "SHA-256 校验失败，停止安装" }
tar.exe -xzf $archive -C $workDir
if ($LASTEXITCODE -ne 0) { throw "归档解压失败，停止安装" }
& openclaw skills install (Join-Path $workDir "image-intake-router-3.1.0\image-intake-router") --global --as image-intake-router
if ($LASTEXITCODE -ne 0) { throw "OpenClaw Skill 安装失败" }
```

### Linux / NAS shell

```bash
set -euo pipefail
work_dir="$(mktemp -d)"
archive="$work_dir/image-intake-router-3.1.0.tgz"
checksum="$archive.sha256"
curl -fL -o "$archive" https://github.com/Aim996/image-intake-router/releases/download/v3.1.0/image-intake-router-3.1.0.tgz
curl -fL -o "$checksum" https://github.com/Aim996/image-intake-router/releases/download/v3.1.0/image-intake-router-3.1.0.tgz.sha256
(cd "$work_dir" && sha256sum -c image-intake-router-3.1.0.tgz.sha256)
tar -xzf "$archive" -C "$work_dir"
openclaw skills install "$work_dir/image-intake-router-3.1.0/image-intake-router" --global --as image-intake-router
```

哈希不一致时立即停止；不能用文件存在、下载命令成功或 shell 无报错代替 SHA-256 校验。NAS GUI 用户也应先在可信终端完成校验。

## 多设备源码克隆/拉取

需要维护公开源码副本时，每台设备可使用：

```bash
git clone https://github.com/Aim996/image-intake-router.git
git -C image-intake-router fetch --tags --prune
git -C image-intake-router checkout --detach v3.1.0
```

已有克隆先运行 `git -C image-intake-router switch main` 和 `git -C image-intake-router pull --ff-only origin main` 更新公开源码，再 `fetch --tags` 并切回经过验证的固定 `v3.1.0` tag。正式安装优先使用上面的固定 Release 与 checksum，不能把 `main`、`latest` 或未验证提交当成 3.1.0 资产。

## 安装布局与旧版恢复材料

命令只把嵌套目录 `image-intake-router-3.1.0/image-intake-router/` 安装为 `image-intake-router`；外层归档目录不是 Skill。全局安装由 OpenClaw 管理到有效的 `<OPENCLAW_SKILLS_DIR>/image-intake-router/`。

升级前，把现有 Skill 目录备份到扫描根目录之外并保留 OpenClaw 配置。即时回滚目标是不可变的 [v3.0.0 Release](https://github.com/Aim996/image-intake-router/releases/tag/v3.0.0)、`image-intake-router-3.0.0.tgz` 和 `image-intake-router-3.0.0.tgz.sha256`；更早的稳定目标是不可变的 [v2.1.0 Release](https://github.com/Aim996/image-intake-router/releases/tag/v2.1.0)、`image-intake-router-2.1.0.tgz` 和 `image-intake-router-2.1.0.tgz.sha256`。不要重命名或删除旧 tag、archive 或 checksum；恢复前重新核验对应 checksum，只替换 Skill 目录与配置。

路由器没有下游业务数据库。v3 安装和回滚都不迁移、修改或删除随手账、食序管家或其他下游数据，也不要求下游仓库/API 变化。

启用新 Skill 前停用会重复识图的旧入口 `food-image-intake`，重载 OpenClaw 配置，并保留旧 Skill 目录直到验收结束。

## 业务级 UAT

1. 上传两张或更多图片，验证每张图片都有一次初次真实视觉识别；文件名和描述不能单独形成事实。
2. 使用初次结果遗漏一个可见字段的样本，验证只进行最多一次补充识读；没有遗漏时不补充识读。
3. 用九商品订单验证简化名称、规格/数量/行实付、真实 `¥0.00` 和可靠生产日期；退款、短重、原价、优惠、费用、会员与赠品推测不得出现在预览或 handoff。
4. 验证初始含图回合依次显示 `【入账】`、`【入库】`、可选 `【需确认】`；商品行只列一次，全部可入库时显示“以上 N 种食品均入库”，并创建零次交接。
5. 上传折叠、遮挡、裁切、模糊或不可读样本：问题必须披露、不得猜测；可靠可见内容仍应可用。
6. 在后续回合分别测试普通肯定确认、`只记账`、`只入库` 和重复确认；每个预览最多创建一次 OpenClaw handoff。
7. 验证 OpenClaw 负责发现/调用下游 Skill；路由器不检查或修改下游项目、私有 API、端口、接口、数据库、数据、重试/状态行为或适配协议。

通过业务验收后才把 3.1.0 作为使用版本。若不通过，按 [更新与回滚](UPGRADING.md) 恢复 v3.0.0 或 v2.1.0 Skill 与配置，不修改下游数据。
