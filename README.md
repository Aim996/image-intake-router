# image-intake-router

`image-intake-router` 3.0.0 is a local OpenClaw Skill for payment screenshots, receipts, order pages, nutrition labels, food packages, grocery screenshots, and meal photos. Its schema is `image-intake-router.v3`.

The router owns focused image recognition and confirmation: every image gets one initial visual pass, followed by at most one omission-driven targeted refinement when needed. It cleans visible text into one canonical fact set, audits visible fields, and produces a detailed preview in the exact order `【入账内容】`, `【入库内容】`, `【需要注意】`.

The initial image turn only previews and creates zero handoffs. A later affirmative confirmation creates at most one handoff; `只记账` and `只入库` limit its scope. OpenClaw discovers and invokes downstream Skills. The router does not own downstream execution, inspect or modify downstream projects/private APIs/databases, or define private adapter payloads, ports, retries, or status protocols.

Hidden, blocked, cropped, blurred, or unreadable content is disclosed rather than guessed. Reliable visible content remains usable, including visible-only handoff when other items are hidden. Version 3 does not migrate, modify, or delete downstream data and requires no downstream repository or API changes.

## Install and safe rollback

Install the exact v3 assets `image-intake-router-3.0.0.tgz` and `image-intake-router-3.0.0.tgz.sha256` by following [the installation guide](docs/INSTALL.md). It includes SHA-256 verification, Windows PowerShell, Linux/NAS commands, the nested Skill layout, and business-level UAT. Multiple devices can repeat the same fixed GitHub Release commands independently.

Keep the immutable [v2.1.0 release](https://github.com/Aim996/image-intake-router/releases/tag/v2.1.0), exact assets `image-intake-router-2.1.0.tgz` and `image-intake-router-2.1.0.tgz.sha256`, the verified old Skill directory, and the prior OpenClaw configuration as the rollback target. Follow [the upgrading guide](docs/UPGRADING.md) to restore them without touching downstream data. Old tags and assets must not be renamed or deleted.

For the complete public behavior, see [识图输出与确认规范](识图输出与确认规范.md). For OpenClaw media behavior, see the official [media-understanding guide](https://github.com/openclaw/openclaw/blob/main/docs/nodes/media-understanding.md) and [media overview](https://docs.openclaw.ai/tools/media-overview).

## Data boundary

The router does not store original images, paths, base64, full OCR, credentials, or local business databases. It does not migrate, modify, delete, retry, or query downstream data. Downstream Skills own their validation, execution, storage, recovery, and compatibility.

## Development checks

```powershell
python -m unittest discover -s tests -p 'test_*.py' -v
python -m unittest discover -s image-intake-router/tests -p 'test_*.py' -v
```

## License

[MIT](LICENSE)
