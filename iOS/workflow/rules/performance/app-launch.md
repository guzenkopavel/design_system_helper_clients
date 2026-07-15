# App launch performance

Различать cold/warm/resume и измерять только определённый сценарий. Найти
фактический entry/composition path и обязательные dependencies.

- Удалить синхронный disk/network I/O с critical path, если данные не нужны до
  первого usable state.
- Не переносить correctness-critical initialization в unowned background task.
- Lazy work имеет owner, cancellation и single-flight semantics.
- Static/global initialization учитывается в trace, а не игнорируется.
- Logging/signposts не раскрывают данные и не меняют измеряемое поведение
  существенно.

Нет универсального «kill threshold» для приложения. Budget задаётся продуктом
или baseline и проверяется на сопоставимом device/build. Simulator/debug trace
используется для diagnosis, но terminal performance evidence выбирается по риску.
