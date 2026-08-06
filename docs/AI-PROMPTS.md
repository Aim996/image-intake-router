# image-intake-router 3.1.0 操作提示词

## 全新安装提示词

```text
请安装 image-intake-router 3.1.0：从固定 v3.1.0 GitHub Release 下载 image-intake-router-3.1.0.tgz 和 .sha256，核验 SHA-256，只安装嵌套 image-intake-router/ Skill 目录。配置真实图片能力和 all 附件模式，停用重复识图旧入口。不要修改下游项目、私有 API 或数据库，也不要迁移、修改或删除下游数据。
```

## 安全更新提示词

```text
请安全更新 image-intake-router 到 3.1.0：先保留固定 v3.0.0、v2.1.0 Release/资产、已验证旧 Skill 和 OpenClaw 配置，再下载并核验 v3.1.0 资产。已有源码克隆可先在 main 执行 git pull --ff-only origin main，但正式安装必须使用固定 tag/Release。若 UAT 失败，只恢复旧 Skill 与配置，不覆盖下游数据库。
```

## UAT 提示词

```text
请验收 image-intake-router 3.1.0 / image-intake-router.v3.1：验证每张图片一次初次真实视觉识别；可见字段遗漏时最多一次补充识读；商品名称简化但全名仍用于证据/去重；只保留最终实付和行实付；可靠生产日期进入入库内容；退款/原价/优惠/会员/费用与赠品推测不进入预览或 handoff；商品列表只列一次并按【入账】【入库】【需确认】输出；图片回合零交接，后续确认最多一次。OpenClaw 负责发现和调用下游 Skill，路由器不修改下游项目、接口、数据库或数据。
```
