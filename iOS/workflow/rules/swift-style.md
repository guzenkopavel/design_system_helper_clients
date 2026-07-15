# Swift style

Первичный стиль определяется существующим formatter/linter/compiler settings и
соседним production-кодом. При отсутствии настройки применяются эти безопасные
defaults; они provisional до появления командного решения.

## Код

- Имена следуют Swift API Design Guidelines: call site читается как фраза,
  labels несут смысл, abbreviations устойчивы в codebase.
- `let` по умолчанию; mutation локальна и имеет одного владельца.
- Access control минимален; `public/open` добавляется только для реального
  module/consumer contract.
- Force unwrap/cast/try допустим только для доказанного programmer invariant с
  локально понятной причиной; runtime input обрабатывается безопасно.
- `guard` используется для preconditions/early exit, `if` — для симметричных
  ветвей; сложные expressions получают имена.
- Extensions группируют conformance или одну cohesive тему. Не дробить тип на
  декоративные секции без ownership benefit.
- File header, imports order и trailing syntax следуют найденному tooling; не
  добавлять copyright или generated marker по догадке.

## API и типы

Prefer domain value types, typed errors и exhaustive enums. Optional означает
реальное отсутствие, не универсальный failure channel. Default arguments не
скрывают важную policy. Public async API документирует cancellation и actor
isolation.

Swift language semantics зависят от compiler и language-mode settings каждого
target. Availability и concurrency fixes проверяются на фактической build
matrix; установленная версия IDE сама по себе ничего не гарантирует.
