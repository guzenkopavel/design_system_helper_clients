---
name: elaborate
description: Вручную провести продуктовую фичу через discovery, shared UX для UI scope, product review lenses и явный human approval до общей READY-спеки для iOS/Android, затем остановиться перед платформенным fan-out.
---

# Elaborate

Полностью выполнить каноническую фазу
[`workflow/phases/elaborate.md`](../../../workflow/phases/elaborate.md).
Также полностью выполнить
[`product-spec-review.md`](../../../workflow/rules/product-spec-review.md).

Это manual-only no-code driver. Без явного human approval сохранить
`DRAFT / PENDING APPROVAL`; не считать молчание одобрением. После `READY`
остановиться: не создавать iOS или Android implementation specs и не запускать
реализацию. Не коммитить без явной просьбы.

После approval переснять fingerprint и запустить ровно шесть final lenses через
отдельные fresh `product-spec-reviewer` contexts в одном parent review session;
сохранить runtime-issued invocation evidence для каждого вызова. JSON содержит
provenance attestation, но не доказывает runtime isolation. Same-context или
unavailable-evidence fallback — `UNKNOWN`, не PASS. Receipt агрегирует только
coordinator; exact valid GAP/UNKNOWN сохраняются в non-green receipt, а READY
разрешён лишь после `validate-product-spec.py check`.
