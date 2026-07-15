# Apple SDK design checks

При применимости design обязан фиксировать:

- Networking: фактическая session configuration/cache policy, freshness,
  redirects и trust policy; user fragments percent-encoded, routing не строится
  на substring.
- File system: user documents → Documents; service data → Application Support;
  disposable → Caches/tmp; backup policy явна.
- Concurrency: continuation single-resume и resume outside lock; synchronous
  publisher emission; cancellation is cooperative; actor state перечитывается
  после `await`; I/O/await под lock запрещены.
- UIKit/SwiftUI lifecycle: реальный scene/URL entry, presentation host и state
  restoration.
- Foundation: mutable formatter/encoder sendability и locale-sensitive compare.
- Correlation: reference ID берётся из реального entity, не свежего UUID.

Дополнительно проверить ownership delegates/observers, retain cycles в escaping
closures, scene transitions, background expiration, notification cleanup,
Keychain/file protection для чувствительных данных и availability guards.

`Codable` mapping не предполагает автоматическую нормализацию дат, ключей или
missing/null: strategy и compatibility fixtures выводятся из реального
контракта. `JSONDecoder`/formatter не объявляется Sendable или thread-safe без
актуальной документации и выбранной модели владения.

Современное SDK behavior, privacy manifests, permissions и UI appearance
исследуются по текущему deployment target/toolchain; список не фиксирует
универсальную версию платформы.

`build succeeded` не доказывает runtime/UI correctness; применимый риск получает
unit/integration/simulator evidence.
