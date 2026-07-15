# Coroutines and Flow

Для выбранного concurrency scope structured concurrency, cancellation
propagation и lifecycle-aware collection являются strong defaults. Dispatcher
boundary применяется там, где этого требует API behavior. Альтернатива требует
evidence/rationale; Flow ownership, hot/cold semantics и error handling остаются
явными.
