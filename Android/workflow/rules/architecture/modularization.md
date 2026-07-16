# Android modularization

Канон адаптирует official Android guidance по
[modularization](https://developer.android.com/topic/modularization) и
[common patterns](https://developer.android.com/topic/modularization/patterns):
high cohesion, low coupling, strict visibility и ясное ownership. Сначала
обнаружить `settings`/Gradle graph, application module, consumers и plugins;
имена modules, tasks и variants не предполагать.

Новая independent feature, domain data capability, networking/transport,
persistence/storage и reusable UI/design-system capability по strong default
изолируется в `Gradle Android library module` или `Gradle Kotlin library module`
с минимальным public contract. Application module не является допустимым
physical unit isolation/deviation.
Feature modules зависят от data contracts/modules. Data module экспортирует
repository contract и скрывает remote/local data sources. Transport не владеет
domain semantics; feature не обращается к source напрямую.

Обнаруженный application module (в текущем типовом layout `:app`) содержит
только entry point, root navigation, lifecycle, DI/dependency wiring,
configuration и target resources. Он зависит от feature capabilities и
компонует implementations, но не владеет feature/domain/data/network logic или
mutable state.

Dependencies ацикличны; consumers зависят от contracts. API/implementation
modules разделяются только при evidence нескольких implementations/consumers,
независимого ownership, visibility или testability — это не обязательный split
для каждого capability.

## Granularity и deviation

Folder/package name не является physical module. Не создавать module на каждую
папку, class или horizontal layer: слишком fine-grained graph увеличивает build
configuration/boilerplate; слишком coarse возвращает monolith. Tiny
one-consumer local behavior может получить `not-applicable`, если cohesion и
отсутствие ownership/testability/visibility benefit доказаны.

`deviation` требует existing/discovered library unit из adapter list, точного
repository/build constraint evidence, typed contract seam, rationale/trade-offs,
migration boundary и objective trigger. Application module никогда не является
deviation. «Быстрее», «один module», малый репозиторий или существующий monolith
сами по себе не достаточны.

Plan называет обнаруженные module/project wiring, public API/visibility tests,
module-level tests, consumer integration/build, dependency graph и app-shell
composition. Verify получает realized graph/tooling evidence; недоступность
обязательной проверки даёт `UNKNOWN`.
