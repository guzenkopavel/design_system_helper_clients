# iOS unit testing

Domain/use-case/state transitions тестировать детерминированно через injected
fakes. Один test — один behavior; Given/When/Then; async completion наблюдается,
timeouts не заменяют signal. Проверить success, domain errors, cancellation,
retry/idempotency и state recovery. Tests не зависят от сети, wall clock,
singleton state или порядка других tests.
