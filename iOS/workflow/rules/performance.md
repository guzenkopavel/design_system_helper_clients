# iOS performance

Performance scope выбирается только при observable risk или explicit budget.
Сначала измерение, затем hypothesis и минимальное изменение; общие «ускорения»
без baseline запрещены.

| Область | Правило |
|---|---|
| Method | [`performance/measure-first.md`](performance/measure-first.md) |
| Launch | [`performance/app-launch.md`](performance/app-launch.md) |
| Concurrency | [`performance/concurrency.md`](performance/concurrency.md) |
| Memory | [`performance/memory.md`](performance/memory.md) |
| Networking | [`performance/networking.md`](performance/networking.md) |
| Profiling | [`performance/profiling.md`](performance/profiling.md) |
| SwiftUI rendering | [`performance/swiftui-rendering.md`](performance/swiftui-rendering.md) |

Budget содержит metric, units, scenario, device/runtime/build configuration,
sample method и допустимую variance. Debug simulator result не переносится на
release device без оговорки. Plan отделяет функциональную корректность от
performance acceptance; verify сохраняет fresh comparable evidence.
