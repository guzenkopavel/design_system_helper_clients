# Shared product specifications

Для каждой фичи общий продуктовый пакет хранится в
`specs/product/<feature>/`: опциональный `concept.md`, `brief.md`, UI-only
`ux.md`, итоговый `spec.md` и coordinator-owned `review-verdicts.json`. Этот
пакет одинаков для iOS и Android. `READY` требует applicable reviews и явного
human product approval с evidence.

После approval `$elaborate` переснимает fingerprint и запускает ровно шесть
fresh read-only `product-spec-reviewer` contexts в одном parent session.
Coordinator хранит runtime invocation evidence; JSON attestation сама по себе
не доказывает isolation. Current PASS/GAP/UNKNOWN findings живут в durable receipt;
spec содержит только static receipt/UX links. Любая package-правка кроме exact
Status metadata делает receipt stale. Без `validate-product-spec.py check: PASS`
platform fan-out запрещён.

Правила слоёв: [`specification-layers.md`](../../workflow/rules/specification-layers.md).
Шаблоны: [`product-concept.md`](../../workflow/templates/product-concept.md),
[`product-brief.md`](../../workflow/templates/product-brief.md) и
[`product-ux.md`](../../workflow/templates/product-ux.md),
[`product-spec.md`](../../workflow/templates/product-spec.md).

Архив product SSOT находится только в
`specs/product/_archive/<feature>/<archive-id>/`; `_archive` исключён из active
discovery. Архивация требует отдельный retirement request, переносит весь пакет
как единицу и оставляет `specs/product/<feature>/spec.md` tombstone. Она не
переписывает platform packages.
