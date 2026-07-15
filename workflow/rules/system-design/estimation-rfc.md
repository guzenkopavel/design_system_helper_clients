# Work items and estimation

Каждый work item относится ровно к одному layer, имеет явный done-state и
занимает не более 2 ideal dev-days. Cross-layer dependency отражается DAG edge,
а не скрывается внутри задачи.

Оценка — range. Базовая оценка отдельно показывает применимые множители:

- unknown unknowns ×1.3–1.5;
- secondary requirements ×1.4–1.7;
- unfamiliar area ×1.5–2.0;
- parallel external API ×1.3–1.4;
- binary distribution ×1.2;
- store review отдельным календарным диапазоном.

Не давать happy-path-only point estimate, не объединять iOS/Android, не скрывать
integration risk. RFC для Extended включает context, landscape, decisions,
alternatives, architecture, data/control flow, risks, migration, verification и
rollout.
