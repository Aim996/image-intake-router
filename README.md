# image-intake-router

`image-intake-router` 3.1.0 is a local OpenClaw Skill for payment screenshots, receipts, order pages, nutrition labels, food packages, grocery screenshots, and meal photos. Its schema is `image-intake-router.v3.1`.

The router performs one initial real visual pass for every image and at most one omission-driven targeted refinement. It builds one canonical fact set, keeps visible full names only for evidence/deduplication, uses concise product names for business content, records actual paid amounts and reliable visible production dates, and renders a compact `【入账】` / `【入库】` / `【需确认】` preview.

The initial image turn creates zero handoffs. A later affirmative confirmation creates at most one handoff; `只记账` and `只入库` limit scope. OpenClaw discovers and invokes downstream Skills. The router does not own downstream execution, inspect or modify downstream projects/private APIs/databases, or define private adapter payloads, ports, retries, or status protocols.

Refund/cancellation text is transient validity input: a partially refunded received item remains eligible, while a fully refunded/cancelled/not-received item is excluded. Refund amounts, original/unit prices, discounts, fee breakdowns, member benefits, and free/gift explanations are absent from facts, preview content, and handoff content.

## Install and safe rollback

Install the exact v3.1 assets `image-intake-router-3.1.0.tgz` and `image-intake-router-3.1.0.tgz.sha256` by following [the installation guide](docs/INSTALL.md). It includes SHA-256 verification, Windows PowerShell, Linux/NAS commands, the nested Skill layout, source-update commands, and business-level UAT.

Keep both previous immutable releases as rollback targets:

- [v3.0.0 release](https://github.com/Aim996/image-intake-router/releases/tag/v3.0.0): `image-intake-router-3.0.0.tgz` and `image-intake-router-3.0.0.tgz.sha256`.
- [v2.1.0 release](https://github.com/Aim996/image-intake-router/releases/tag/v2.1.0): `image-intake-router-2.1.0.tgz` and `image-intake-router-2.1.0.tgz.sha256`.

Follow [the upgrading guide](docs/UPGRADING.md) to restore a fixed version without touching downstream data. Old tags and assets must not be renamed, deleted, or overwritten.

For complete public behavior, see the version-pinned [识图输出与确认规范](https://github.com/Aim996/image-intake-router/blob/v3.1.0/%E8%AF%86%E5%9B%BE%E8%BE%93%E5%87%BA%E4%B8%8E%E7%A1%AE%E8%AE%A4%E8%A7%84%E8%8C%83.md). For OpenClaw media behavior, see the official [media-understanding guide](https://github.com/openclaw/openclaw/blob/main/docs/nodes/media-understanding.md) and [media overview](https://docs.openclaw.ai/tools/media-overview).

## Data boundary

The router does not store original images, paths, base64, full OCR, credentials, or local business databases. It does not migrate, modify, delete, retry, or query downstream data. Downstream Skills own validation, execution, storage, recovery, and compatibility.

## Development checks

```powershell
python -m unittest discover -s tests -p 'test_*.py' -v
python -m unittest discover -s image-intake-router/tests -p 'test_*.py' -v
```

## License

[MIT](LICENSE)
