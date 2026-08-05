# image-intake-router 2.1.0 操作提示词

## 全新安装提示词

```text
请安装 image-intake-router 2.1.0：下载固定 2.1.0 归档和 SHA-256，先核验哈希，只把嵌套 Skill 目录安装到新的目录。配置真实图片能力（原生视觉模型或 tools.media 图片提供方），设 tools.media.image.attachments.mode: "all" 并设置足够 maxAttachments；不要在 tools.media.models[] 内联 API key。停用会重复读图的旧入口，重载后完成多附件业务 UAT。任何附件没有真实视觉结果时必须失败关闭，不预览、不写入；不得仅凭文件存在或 shell 输出声称成功。
```

## 安全更新提示词

```text
请安全更新 image-intake-router 到 2.1.0：保留 v2.0.1 Skill 目录、配置和 Release 资产作为回滚目标；并行安装、核验 SHA-256、配置 all 附件视觉处理后，完成每附件一次视觉运行、部分图片如实披露、初始零业务写入和一次业务确认的 UAT。不得覆盖数据库；适配器技术修复不得重复确认或重复写入。
```

## UAT 提示词

```text
请验收 image-intake-router 2.1.0 / image-intake-router.v2.1：用多张订单截图验证每个附件恰好一次真实视觉能力；附件描述或文件名不能产生事实；任一失败或未执行时无预览、无写入；折叠图片如实显示可见数和隐藏数、不猜测；首回合零业务写入，后续只有一次业务确认，技术修复不重复写入；默认回复简洁，详细字段按需展开。
```
