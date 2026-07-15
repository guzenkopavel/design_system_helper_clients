# Concurrency performance

Concurrency применяется для overlap независимой работы или bounded CPU
parallelism после измерения. Она не исправляет медленный algorithm автоматически.

- Зафиксировать dependency DAG и сохранить required ordering.
- Ограничить fan-out согласно ресурсу/service limits; unbounded task creation
  запрещён.
- Измерять contention, actor hops, suspension count и cancellation waste.
- Не удерживать locks через await/I/O; critical section минимальна.
- Task priority не гарантирует порядок и не заменяет backpressure.
- Проверить energy/thermal/memory cost вместе с latency.

Compiler isolation behavior зависит от target settings. Optimization не может
использовать unsafe Sendable/isolation escape без отдельного correctness proof.
