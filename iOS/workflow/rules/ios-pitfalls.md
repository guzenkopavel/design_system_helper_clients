# Apple SDK design checks

При применимости design обязан фиксировать:

- Networking: cache policy (`URLSession.default` cache включён), freshness,
  pinning; user fragments percent-encoded, routing не строится на substring.
- File system: user documents → Documents; service data → Application Support;
  disposable → Caches/tmp; backup policy явна.
- Concurrency: continuation single-resume и resume outside lock; synchronous
  publisher emission; cancellation is cooperative; actor state перечитывается
  после `await`; I/O/await под lock запрещены.
- UIKit/SwiftUI lifecycle: реальный scene/URL entry, presentation host и state
  restoration.
- Foundation: mutable formatter/encoder sendability и locale-sensitive compare.
- Correlation: reference ID берётся из реального entity, не свежего UUID.

`build succeeded` не доказывает runtime/UI correctness; применимый риск получает
unit/integration/simulator evidence.
