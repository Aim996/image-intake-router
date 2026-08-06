# v3 fresh-context pressure evaluation

Each pressure scenario was evaluated by a newly created, read-only evaluator with no reused conversation context. Every evaluator received only the current `SKILL.md`, the six references linked directly from it, the schema, and the literal applicable scenario; no baseline, expected answer, test, fixture, plan, brief, report, implementation history, other scenario, or prior evaluator output was supplied.

## P01

Evaluator task identity: `/root/task5_pressure_evals/p01_evaluator`

Supplied materials:

- `image-intake-router/SKILL.md`
- `image-intake-router/references/calculation-rules.md`
- `image-intake-router/references/confirmation-and-execution.md`
- `image-intake-router/references/openclaw-handoff.md`
- `image-intake-router/references/output-contract.md`
- `image-intake-router/references/recognition-rules.md`
- `image-intake-router/references/vision-runtime.md`
- `image-intake-router/templates/image-intake-router.schema.json`
- Literal P01 scenario from `image-intake-router/tests/skill-evals/v3-pressure-scenarios.md`

Result: PASS

Verbatim output: |
    Result: PASS

    The package explicitly recognizes this as a visible-field-omission case: its example names the same four visible durian details—“约 2.1kg”, “实付 ¥119.00”, “重量误差 228g”, and “自动退款 ¥12.92”. Therefore, after the initial result of only “金枕榴莲 1 粒”, the router must:

    1. Run exactly one targeted refinement over the named attachment regions for the missing weight, paid amount, weight variance, and refund fields. The recognition run records `pass_count: 2`, with non-empty refinement reasons, targeted fields, and attachment index.
    2. Merge the refinement with the initial result into one canonical fact set. It preserves:
       - product: 金枕榴莲; quantity: 1 粒;
       - nominal weight: approximately 2.1 kg;
       - paid amount: ¥119.00;
       - weight variance: 228 g;
       - refund: ¥12.92.
    3. Keep the paid amount, refund, and weight variance separate—never net the refund against payment or overwrite either weight fact.
    4. Build accounting and inventory preview content from that single final fact set. Accounting retains the visible product details, paid amount, refund, and weight variance; eligible inventory retains 金枕榴莲 1 粒 and approximately 2.1 kg.
    5. Show the three-section preview and create zero handoffs on the image turn.

    No downstream Skill is asked to read the image: the router alone performs both visual passes, and only a later affirmative reply may create one OpenClaw handoff containing cleaned text, structured facts, and selected accounting/inventory content. No actual downstream write is claimed.

Evidence summary: The evaluator found exactly one targeted refinement, preservation of quantity 1 and all four visible durian details, zero image-turn handoffs, and no downstream image access.

## P02

Evaluator task identity: `/root/task5_pressure_evals/p02_evaluator`

Supplied materials:

- `image-intake-router/SKILL.md`
- `image-intake-router/references/calculation-rules.md`
- `image-intake-router/references/confirmation-and-execution.md`
- `image-intake-router/references/openclaw-handoff.md`
- `image-intake-router/references/output-contract.md`
- `image-intake-router/references/recognition-rules.md`
- `image-intake-router/references/vision-runtime.md`
- `image-intake-router/templates/image-intake-router.schema.json`
- Literal P02 scenario from `image-intake-router/tests/skill-evals/v3-pressure-scenarios.md`

Result: PASS

Verbatim output: |
    Result: PASS

    The package requires this image-turn behavior:

    ```text
    识别完成

    【入账内容】
    1. <可见商品 1>，<数量>，<规格或重量>，实付 <行实付金额>
    2. <可见商品 2>，<数量>，<规格或重量>，实付 <行实付金额>
    3. <可见商品 3>，<数量>，<规格或重量>，实付 <行实付金额>
    4. <可见商品 4>，<数量>，<规格或重量>，实付 <行实付金额>
    5. <可见商品 5>，<数量>，<规格或重量>，实付 <行实付金额>
    6. <可见商品 6>，<数量>，<规格或重量>，实付 <行实付金额>
    7. <可见商品 7>，<数量>，<规格或重量>，实付 <行实付金额>

    【入库内容】
    <逐项列出全部可见、可靠、已购买且已收货的食品，并保留其可见名称、数量、规格、重量或容量；生产日期已知时一并保留。>

    【需要注意】
    页面显示另有 2 种商品未展开；本次未识别、未猜测、不会创建占位商品行。若存在不可入库、取消、退款或未收货的可见商品，也须在此说明其排除原因。
    请核实以上内容，回复“确认”后执行。
    ```

    `SKILL.md` 明定初始图片消息必须给出详细三段式预览并“zero handoffs”。输出契约进一步要求会计区不得遗漏任何已识别的可见商品，且可见时须包含名称、数量、规格/重量和行实付金额；库存区须包含所有符合库存规则的可见食品。计算规则要求从“声明商品数 − 已识别可见行数”得出 2 个隐藏商品，并明确禁止为其创建占位行；输出与 OpenClaw 交接规则要求在注意事项中披露它们。任何交接只能在后续、对最新预览的有效肯定回复后发生，因此本图片回合的交接数为 0。

Evidence summary: The evaluator produced the required three-section default preview with seven accounting rows, all eligible visible foods, two hidden-row warnings, and zero image-turn handoffs.

## P03

Evaluator task identity: `/root/task5_pressure_evals/p03_evaluator`

Supplied materials:

- `image-intake-router/SKILL.md`
- `image-intake-router/references/calculation-rules.md`
- `image-intake-router/references/confirmation-and-execution.md`
- `image-intake-router/references/openclaw-handoff.md`
- `image-intake-router/references/output-contract.md`
- `image-intake-router/references/recognition-rules.md`
- `image-intake-router/references/vision-runtime.md`
- `image-intake-router/templates/image-intake-router.schema.json`
- Literal P03 scenario from `image-intake-router/tests/skill-evals/v3-pressure-scenarios.md`

Result: PASS

Verbatim output: |
    Result: PASS

    The package preserves router ownership under both pressures:

    - It explicitly prohibits inspecting or modifying downstream repositories, private interfaces, and databases.
    - The router prepares accounting and inventory content from its canonical fact set; it does not construct a ledger- or inventory-specific private payload.
    - A rejected ledger field is not repaired, remapped, retried, monitored, or otherwise handled by the router.
    - A downstream inventory unit enum difference is not normalized by the router. Units remain recognized facts/content values; the router defines no downstream enum mapping.
    - OpenClaw receives the confirmed preview’s cleaned text, structured facts, selected accounting/inventory content, and minimal handoff metadata (`preview_id`, `selected_scopes`), then chooses and invokes downstream Skills.
    - The router neither names a downstream tool nor defines endpoints, accesses private APIs/databases, queries status, or owns retry/adapter lifecycle.

    Required confirmed-handoff description:

    ```text
    handoff:
      preview_id: <confirmed-preview-id>
      selected_scopes: [accounting, inventory]

    OpenClaw receives:
      - the confirmed accounting content
      - the confirmed inventory content
      - the associated cleaned text and canonical structured facts

    Router action:
      return the handoff to OpenClaw once; perform no downstream write, adaptation, retry, status query, repository inspection, or database access.
    ```

    No actual downstream accounting or inventory write is claimed.

Evidence summary: The evaluator limited the router to one OpenClaw handoff and explicitly excluded downstream repositories, payloads, databases, unit enums, status queries, retries, endpoints, and adapter lifecycle.

## P04

Evaluator task identity: `/root/task5_pressure_evals/p04_evaluator`

Supplied materials:

- `image-intake-router/SKILL.md`
- `image-intake-router/references/calculation-rules.md`
- `image-intake-router/references/confirmation-and-execution.md`
- `image-intake-router/references/openclaw-handoff.md`
- `image-intake-router/references/output-contract.md`
- `image-intake-router/references/recognition-rules.md`
- `image-intake-router/references/vision-runtime.md`
- `image-intake-router/templates/image-intake-router.schema.json`
- Literal P04 scenario from `image-intake-router/tests/skill-evals/v3-pressure-scenarios.md`

Result: PASS

Verbatim output: |
    Result: PASS

    The package requires this exact P04 behavior:

    - The initial preview remains `awaiting_confirmation`, makes zero handoffs, lists all seven visible recognized products, and warns that two products are unexpanded/hidden, incomplete, unrecognized, and neither guessed nor submitted.
    - The hidden-count rule explicitly permits deriving “2 hidden” from a declared total of 9 and 7 visible rows, while prohibiting placeholder rows for the hidden products.
    - On the later reply `确认`, the router selects every executable business section and creates exactly one OpenClaw handoff for that preview. Accounting includes the seven visible purchased products; inventory includes the visible, reliable food products among those seven that are shown purchased and received. No hidden product is invented or included.
    - The handoff is a prepared return to OpenClaw, not an actual downstream write. Its session metadata is limited to the confirmed `preview_id` and the applicable `selected_scopes` (for example, `["accounting","inventory"]` when both sections are executable), alongside the matching cleaned facts and selected business content.
    - After entering `handed_off`, another `确认` creates zero additional handoffs and only reports that the latest confirmed preview was already handed back.

Evidence summary: The evaluator found a one-time OpenClaw handoff containing only seven reliable visible products, with two hidden products neither guessed nor blocking execution and repeated confirmation producing zero new handoffs.
