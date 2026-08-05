# 安装 image-intake-router 2.1.0

## 先准备真实图片能力

在 OpenClaw 中配置真实、支持图片的原生模型，或配置 `tools.media` 的图片提供方。原生主模型只要 OpenClaw 将原始图片传给它，同样可以满足视觉能力。不要把 API key 直接写进 `tools.media.models[]`；请使用正常的 provider/auth 配置。

OpenClaw 的媒体附件策略默认只处理第一个附件。订单有多张截图时，必须设置 `tools.media.image.attachments.mode: "all"`，并设定足够大的 `maxAttachments`。最小 JSON5 示例（提供方和模型由你的正常认证配置决定）：

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

图片能力可能被禁用或不可用，且 OpenClaw 的媒体理解属于 best-effort。因此本 Skill 会自行进行失败关闭的业务验收：任何附件没有真实视觉结果，就不生成业务预览、更不写入账本或库存。请参阅官方 [media-understanding](https://github.com/openclaw/openclaw/blob/main/docs/nodes/media-understanding.md) 与 [media overview](https://docs.openclaw.ai/tools/media-overview)。

## 获取并校验固定资产

发布后只从 2.1.0 Release 下载 `image-intake-router-2.1.0.tgz` 和 `image-intake-router-2.1.0.tgz.sha256`。

### Windows PowerShell

```powershell
Get-FileHash -Algorithm SHA256 .\image-intake-router-2.1.0.tgz
Get-Content .\image-intake-router-2.1.0.tgz.sha256
```

### Linux / NAS shell

```bash
sha256sum -c image-intake-router-2.1.0.tgz.sha256
```

哈希不一致时立即停止；不要以文件存在或 shell 命令无错误代替校验。NAS GUI 用户也应先在可信终端完成 SHA-256 校验。

## 安装布局与恢复

解压后只安装嵌套目录 `image-intake-router-2.1.0/image-intake-router/` 到 `<OPENCLAW_SKILLS_DIR>/image-intake-router/`；外层归档目录不是 Skill。请使用新的并行目录，保留现有 2.0.1 Skill 目录、配置和 [v2.0.1 发布资产](https://github.com/Aim996/image-intake-router/releases/tag/v2.0.1)，以便恢复。路由器没有数据库，安装不创建、覆盖或迁移任何数据库。

启用新 Skill 前停用会重复读图的旧入口 `food-image-intake`，重载 OpenClaw 配置，并保留旧目录直到验收结束。

## 业务级 UAT（失败关闭）

1. 上传两张或更多订单截图：每个附件恰好进入视觉能力一次；文件名和描述不能单独形成事实。
2. 模拟任一附件视觉能力失败或未执行：不得出现预览、确认提示或业务写入。
3. 上传带“还有 N 件”或折叠区域的截图：摘要必须明确可见数和隐藏数，不能猜测隐藏项目。
4. 初始图片回合验证零业务写入；随后只进行一次业务确认。相同业务摘要的适配器修复不再确认，也不重复写入。
5. 默认回复应简洁；只在用户要求时展示完整字段。

通过上述业务验收后才可将 2.1.0 作为使用版本。若不通过，恢复 2.0.1 目录和配置，不修改下游数据。
