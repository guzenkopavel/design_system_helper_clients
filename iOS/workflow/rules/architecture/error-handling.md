# Error handling

External failures выражать domain error, не `nil`/`Bool`. Infrastructure errors
нормализуются на boundary. `try?` допустим только для доказанно необязательного
best-effort; silent catch запрещён. `fatalError` — только programmer invariant,
не runtime/network/storage/user input.

Async task обязан наблюдать/обработать throw. UI получает actionable state без
PII в message/logging context.

## Mapping boundary

- Transport/storage/SDK error сохраняется для diagnostics, но наружу выдаётся
  стабильная domain category.
- Cancellation не маскируется как пользовательская ошибка.
- Retry выполняется только для классифицированного transient failure, имеет
  bounded policy и не дублирует non-idempotent side effect.
- Partial data описывается отдельным результатом, если это допустимый контракт,
  а не случайным `nil`.
- Logging не является handling; caller всё равно получает результат.

UI state различает recoverable action, terminal state и background degradation.
Текст для пользователя локализуется на presentation boundary. Verify включает
минимум одну failure/recovery ветвь для каждой новой integration boundary.
