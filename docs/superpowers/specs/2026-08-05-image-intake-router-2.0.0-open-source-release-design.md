# image-intake-router 2.0.0 开源发布设计

日期：2026-08-05
状态：已完成方案确认，等待书面规格复核
目标仓库：`https://github.com/Aim996/image-intake-router`
目标版本：`2.0.0`
目标标签：`v2.0.0`

## 1. 背景与现状

`image-intake-router` 是面向 OpenClaw 的统一图片识别与双路由 Skill。它对同一批图片只做一次视觉解释，形成统一事实后，默认生成随手账和食序管家两份预览；只有用户明确确认最近一次完整预览后，下游才允许写入。

当前仓库只有一个发布提交，`main` 与 `origin/main` 同步。产品包含 Markdown Skill、六个参考规则、一个 JSON Schema 和 Python 标准库静态契约测试。当前没有第三方运行时依赖、包管理器、编译步骤、数据库或本项目持久化数据，也没有 Tag、GitHub Release、GitHub Actions、LICENSE、CHANGELOG、正式安装文档或升级文档。

现有 2.0.0 产品契约保持不变。本次工作只建立规范的开源、构建、安装、更新、验证和发布边界，不改写识别、投影、确认或失败恢复的业务语义。

## 2. 目标

本次发布必须实现：

1. 版本号在 `VERSION`、README、CHANGELOG、Skill、构建产物和 Release 中一致为 `2.0.0`。
2. 仓库采用 MIT License，并在正式 Release 验证完成后从 Private 改为 Public。
3. 普通用户默认从 GitHub Release 下载固定版本预构建包，不需要克隆源码、安装开发依赖或现场构建。
4. 发布包名称为 `image-intake-router-2.0.0.tgz`，并生成 `image-intake-router-2.0.0.tgz.sha256`。
5. 发布包采用严格白名单，只包含运行时 Skill、Schema、必要文档、版本文件和 License。
6. 发布包在独立临时目录中完成校验、解压、安装和最小冒烟测试。
7. `v2.0.0` 标签触发 GitHub Actions；任一测试、构建或验包步骤失败时不得创建成功 Release。
8. 文档覆盖普通安装、安全更新、回滚、三套 AI 操作提示词、数据安全和开发者验证方式。

## 3. 非目标

本次不做以下事项：

- 不修改随手账或食序管家的代码、数据库、配置或 GitHub 仓库。
- 不引入 npm、Python 包发布、Docker 镜像或常驻服务。
- 不保存或上传原图、完整 OCR、支付账户、凭据、数据库或真实用户数据。
- 不自动启用正在运行的 OpenClaw Skill，也不自动停用旧版 `food-image-intake`。
- 不把测试、构建脚本、缓存或开发机路径放入预构建包。
- 不为无数据库的路由 Skill 虚构数据库备份或迁移流程。

## 4. 仓库结构

源代码仓库新增或规范以下结构：

```text
image-intake-router/
├── .github/workflows/release.yml
├── docs/
│   ├── INSTALL.md
│   ├── UPGRADING.md
│   ├── AI-PROMPTS.md
│   └── superpowers/specs/...
├── image-intake-router/
│   ├── SKILL.md
│   ├── references/
│   ├── templates/
│   └── tests/
├── scripts/
│   ├── build_release.py
│   └── verify_release.py
├── tests/
│   └── test_release_pipeline.py
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── README.md
├── RELEASE_NOTES.md
├── VERSION
├── 后续迭代计划.md
├── 项目说明.md
└── 约束文档.md
```

源仓库保留测试和构建工具；预构建包不照搬整个源仓库。

## 5. 版本模型

`VERSION` 是产品语义版本的唯一机器可读来源，内容严格为一行 `2.0.0`。构建脚本接受可选的 `--version`，但传入值必须与 `VERSION` 完全一致，否则失败。

`image-intake-router.v2` 是统一事实协议版本，不是产品 SemVer。Schema 中的 `$id` 和 `schema_version` 继续使用 `v2`，避免把产品补丁版本误当成协议变更。README、项目说明、CHANGELOG、Skill 的产品版本说明和 Release 标题使用 `2.0.0`。

标签必须是 `v2.0.0`。发布工作流从标签提取 `2.0.0`，与 `VERSION` 比较。标签已存在时停止，不覆盖或移动旧标签。

## 6. 预构建发布包

构建由 Python 标准库脚本完成，不增加第三方依赖。归档根目录固定为 `image-intake-router-2.0.0/`，允许包含：

```text
image-intake-router-2.0.0/
├── VERSION
├── README.md
├── LICENSE
├── CHANGELOG.md
├── docs/
│   ├── INSTALL.md
│   ├── UPGRADING.md
│   └── AI-PROMPTS.md
└── image-intake-router/
    ├── SKILL.md
    ├── references/*.md
    └── templates/image-intake-router.schema.json
```

归档明确排除 `.git`、`.github`、`scripts`、`tests`、`image-intake-router/tests`、缓存、日志、数据库、备份、本地配置、密钥、Token、原图和构建目录。

构建脚本按排序后的白名单写入 tar，统一归档元数据，使同一提交和版本在相同 Python 主版本下得到稳定内容。SHA-256 文件使用标准格式：

```text
<64 位小写哈希>  image-intake-router-2.0.0.tgz
```

## 7. 验包与隔离冒烟测试

`verify_release.py` 对发布包执行以下检查：

1. 文件名、根目录名和 `VERSION` 一致。
2. `.sha256` 与归档实际摘要一致。
3. 归档成员没有绝对路径、`..`、符号链接或硬链接，防止路径穿越。
4. 必需运行时文件全部存在。
5. 禁止目录、扩展名和敏感命名没有进入归档。
6. 归档内 Skill 引用的六个 reference 均可解析。
7. Schema 可由标准 JSON 解析器读取，且协议版本仍为 `image-intake-router.v2`。
8. 解压到全新的临时目录，将 `image-intake-router/` 复制到模拟 OpenClaw Skills 目录。
9. 从模拟安装目录读取 `SKILL.md`、references 和 Schema，确认安装不依赖源代码目录。

该 Skill 没有常驻进程或真实 OpenClaw 测试运行时，因此冒烟测试验证的是可安装结构、入口可读性、引用完整性和 Schema 可解析性。真实模型层图片行为仍由现有静态契约和未来 2.0.1 UAT 计划覆盖，不能用文件存在冒充真实模型验收。

## 8. 安装、更新与回滚

普通安装流程：

1. 从固定的 GitHub Release 下载 `.tgz` 和 `.sha256`。
2. 校验 SHA-256。
3. 解压到临时目录。
4. 确认当前 OpenClaw Skill 根目录。
5. 把包内 `image-intake-router/` 安装为一个独立版本目录或由部署者管理的固定 Skill 目录。
6. 确认旧版 `food-image-intake` 未与新路由同时启用。
7. 重启或重新加载 OpenClaw。
8. 通过真实模型层进行无写入预览验收；未确认时不得调用下游写工具。

更新不会覆盖项目数据，因为本项目没有数据库或持久化数据。更新前仍要记录当前 Skill 版本和安装目录，并保留旧版本目录。失败时停用新版本、恢复旧目录并重新加载 OpenClaw。不得删除随手账或食序管家的数据目录，也不得把下游数据复制进本项目发布包。

## 9. 数据安全

本项目自身无持久化数据目录、数据库迁移或备份目录。路由器只生成会话内规范化事实和确认状态，不保存原图、OCR 全文、支付账户、凭据或下游数据库内容。

文档必须明确区分：

- **程序文件：** GitHub Release 中的 Skill、Schema 和文档。
- **会话状态：** OpenClaw 运行期间的预览与确认状态，不作为仓库或发布包数据。
- **下游业务数据：** 随手账和食序管家各自管理的数据，不由本项目安装、更新或回滚脚本接触。

本次发布的数据库结论固定为：未修改数据库、未执行迁移、无本项目备份目录、未删除任何用户数据。不能使用模糊的“数据正常”替代这些事实。

## 10. GitHub Actions 与 Release

`.github/workflows/release.yml` 只在 `v*` 标签推送时运行，并授予最小的 `contents: write` 权限。流程为：

1. Checkout 标签对应提交。
2. 安装固定主版本 Python。
3. 检查标签版本与 `VERSION` 一致。
4. 运行现有 12 项静态契约。
5. 解析 JSON Schema。
6. 运行发布管线单元测试。
7. 构建 `.tgz` 和 `.sha256`。
8. 验证发布包并执行隔离安装冒烟测试。
9. 使用仓库自带的 GitHub CLI 和 `GITHUB_TOKEN` 创建 Release，上传两个 Assets，并使用 `RELEASE_NOTES.md`。

任何前置步骤失败都会阻止 Release 创建。工作流不得覆盖已存在的 Release 或标签。

## 11. 文档范围

README 面向普通用户，优先展示 Release 安装，不把源码构建作为默认路径。它必须覆盖用途、功能、稳定版本、系统要求、安装、使用、更新、数据位置、安全、回滚、FAQ、开发者验证和 MIT License。

`docs/INSTALL.md` 说明 Release 安装、OpenClaw/NAS/Windows/Linux 路径差异、启用边界、重载和真实模型层验收。`docs/UPGRADING.md` 说明固定版本下载、校验、保留旧版本、更新和回滚。`docs/AI-PROMPTS.md` 提供全新安装、安全更新、安装验收三套可复制提示词，并明确禁止用源码测试或 shell 输出冒充真实功能验收。

CHANGELOG 使用 Added、Changed、Fixed、Security 分类，并明确 2.0.0 不涉及数据库结构变化。`RELEASE_NOTES.md` 包含安装、更新、数据迁移、校验、已知限制和回滚说明。

## 12. 测试策略

本次实施采用测试驱动：先增加失败的发布管线测试，再实现脚本和文档。验证层次为：

- 静态检查：现有 Skill 契约、版本一致性、文档必需章节、敏感文件扫描。
- 单元测试：发布白名单、确定性成员排序、版本拒绝、SHA-256、路径穿越拒绝。
- 集成测试：构建真实发布包，再由验包脚本解压并检查。
- 构建：生成正式命名的 `.tgz` 和 `.sha256`。
- 隔离安装：在临时目录模拟 OpenClaw Skills 根目录，不依赖源目录。
- GitHub 验证：标签工作流成功，Release 页面存在，两个 Assets 可下载且摘要匹配。

没有类型检查器或编译器；最终报告中类型检查明确记为“不适用”，而不是声称通过。

## 13. 发布门禁

只有同时满足以下条件才可报告 2.0.0 正式发布：

- 分支变更只包含本项目文件。
- 所有本地测试、构建、验包和隔离冒烟检查通过。
- `v2.0.0` 在远端创建且此前不存在。
- GitHub Actions 对该标签成功完成。
- GitHub Release 标题、说明和版本一致。
- `.tgz` 与 `.sha256` 两个 Assets 均真实存在且可下载。
- 下载后的 `.tgz` 摘要与 `.sha256` 一致。
- 仓库已改为 Public，MIT License 可见。
- 最终报告逐项列出未验证内容和数据安全事实。

若 GitHub Actions、Release Asset 或下载校验失败，保留失败证据并停止，不把版本描述为已发布，也不移动或覆盖标签。
