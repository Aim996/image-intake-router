# image-intake-router 3.0.0 操作提示词

## 全新安装提示词

```text
请安装 image-intake-router 3.0.0：从固定 v3.0.0 GitHub Release 下载 image-intake-router-3.0.0.tgz 和 .sha256，核验 SHA-256，只安装嵌套 image-intake-router/ Skill 目录。配置真实图片能力和 all 附件模式，停用会重复识图的旧入口。不要修改下游项目、私有 API 或数据库，也不要迁移、修改或删除下游数据。
```

## 安全更新提示词

```text
请安全更新 image-intake-router 到 3.0.0：保留 v2.1.0 Release、image-intake-router-2.1.0.tgz、image-intake-router-2.1.0.tgz.sha256、已验证旧 Skill 和 OpenClaw 配置；并行安装并核验 v3 资产。更新不得要求下游仓库/API 变化。若 UAT 失败，只恢复旧 Skill 与配置，不覆盖下游数据库。
```

## UAT 提示词

```text
请验收 image-intake-router 3.0.0 / image-intake-router.v3：验证每张图片一次初次真实视觉识别；仅在可见字段遗漏时最多一次补充识读；清洗结果形成一个统一事实集；初始含图回合严格按【入账内容】、【入库内容】、【需要注意】展示详细预览且零交接；后续肯定确认最多交接一次；“只记账”和“只入库”限定范围。隐藏、遮挡、裁切、模糊、被阻止或不可读内容必须披露而不能猜测，可靠可见内容仍可使用。OpenClaw 负责发现和调用下游 Skill，路由器不得修改下游项目、私有 API、端口、接口、数据库、数据、重试/状态行为或适配协议。
```
