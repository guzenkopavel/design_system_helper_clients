# iOS unit testing

Domain/use-case/state transitions тестировать детерминированно через injected
fakes. Один test — один behavior; Given/When/Then; async completion наблюдается,
timeouts не заменяют signal. Проверить success, domain errors, cancellation,
retry/idempotency и state recovery. Tests не зависят от сети, wall clock,
singleton state или порядка других tests.

## Test design

- Имя описывает condition и observable result.
- Fake clock, UUID/source of randomness и scheduler вводятся на boundary, когда
  они влияют на поведение.
- Async test ждёт конкретный signal/state; произвольный timeout остаётся только
  верхней защитой от зависания.
- Mock interactions проверяются лишь когда ordering/call count является
  контрактом. В остальных случаях проверяется output/state.
- Parameterized cases используются для таблиц правил; один giant test с
  несколькими причинами падения избегается.
- Regression test сначала воспроизводит дефект и падает ожидаемо.

Выбирать XCTest, Swift Testing или другой найденный framework по существующему
target/toolchain. Семантика parallelization, traits и isolation подтверждается
актуальной конфигурацией, а не предполагается.
