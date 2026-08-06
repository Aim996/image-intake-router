# image-intake-router

`image-intake-router` is a local OpenClaw Skill for payment screenshots, receipts, order pages, nutrition labels, food packages, grocery screenshots, and meal photos. Version **2.1.0** uses a real pixel/media recognition run once per attachment batch, builds unified detailed facts, then creates an expense projection and a pantry projection without reading the images again.

## Current version and safe rollback

The current product version is **2.1.0** and its protocol is `image-intake-router.v2.1`. Install the exact assets from the 2.1.0 release when it is published: `image-intake-router-2.1.0.tgz` and `image-intake-router-2.1.0.tgz.sha256`.

Keep the immutable [v2.0.1 release](https://github.com/Aim996/image-intake-router/releases/tag/v2.0.1), its `image-intake-router-2.0.1.tgz` and checksum, and the prior OpenClaw configuration as a rollback target. Do not overwrite an existing Skill directory or a downstream database while updating.

## What changes for users

- A batch has one true visual recognition run; attachment filenames and descriptions do not create facts.
- Unified facts retain product names, specifications, quantities, paid amounts, refunds, merchant, time, order status, source, confidence, calculations, and image completeness.
- The expense adapter receives scalar line items with name, specification, quantity, paid amount, and refund detail. The pantry adapter consumes the same facts without a second image read.
- The initial image turn makes zero business writes and gives one concise preview. A later business confirmation is required once; adapter-only technical repair uses the same digest and does not ask again or duplicate writes.
- A failed or missing visual result for any attachment fails closed: no preview and no business write. Folded or incomplete screenshots state visible and hidden counts without guessing hidden products.

## Install and validate

Follow [the installation guide](docs/INSTALL.md) to verify SHA-256, configure real image media, install only the nested Skill directory, and perform the business-level UAT. Follow [the upgrading guide](docs/UPGRADING.md) for side-by-side installation and rollback.

For OpenClaw media behavior, see the official [media-understanding guide](https://github.com/openclaw/openclaw/blob/main/docs/nodes/media-understanding.md) and [media overview](https://docs.openclaw.ai/tools/media-overview).

## Data boundary

The router does not store original images, paths, base64, full OCR, credentials, or local business databases. It routes confirmed public facts to downstream Skills; those Skills own their own local data. Unsupported business cases include income, balances, transfers, loans, investments, assets, guessed hidden products, and writing anything from a visual run that is absent or incomplete.

## Integrating other software

The router publishes facts and an adapter contract; it does not take ownership of a downstream repository, API, or database. Downstream maintainers implement the adapter in their own project or in a separate integration project. See the Chinese [external software adapter contract](适配接口规范.md) for capability discovery, preflight, one-confirmation execution, idempotency, status recovery, versioning, and the explicit ownership boundary.

## Development checks

```powershell
python -m unittest discover -s tests -p 'test_*.py' -v
python -m unittest discover -s image-intake-router/tests -p 'test_*.py' -v
```

## License

[MIT](LICENSE)
