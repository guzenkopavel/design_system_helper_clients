# Error handling

External failures выражать domain error, не `nil`/`Bool`. Infrastructure errors
нормализуются на boundary. `try?` допустим только для доказанно необязательного
best-effort; silent catch запрещён. `fatalError` — только programmer invariant,
не runtime/network/storage/user input.

Async task обязан наблюдать/обработать throw. UI получает actionable state без
PII в message/logging context.
