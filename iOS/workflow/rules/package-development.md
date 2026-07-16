# iOS physical modularity

Сначала обнаружить реальный project/workspace layout, target membership,
manifest (если он есть), products, targets, supported platforms, dependency
graph и consumers. Physical unit выбирается из exact adapter list: `Swift
package`, `Swift package target` или `non-application Xcode target`.
Application target не является unit isolation/deviation. Наличие `Package.swift`
не предполагается, пути и команды не изобретаются.

Новая feature, domain data/repository capability, networking/transport,
persistence/storage и reusable UI/design-system capability по strong default
получает отдельный physical unit и минимальный public contract. Application
target оставляет только entry point, lifecycle, root navigation/routing,
dependency registration/DI, target configuration и target-specific resources.
Он компонует implementations, но не владеет feature/domain/data/network
implementation или mutable state.

- Product/API surface минимален; implementation types остаются internal.
- Target dependencies ацикличны и направлены от policy к details через
  contracts.
- Consumers импортируют public contract, а не concrete implementation details;
  feature не обращается к transport/persistence source напрямую.
- Resources объявлены в manifest и проверены через consumer-compatible access.
- Platform-specific code изолирован availability/conditional compilation с
  тестом каждой поддерживаемой ветви.
- Dependency version policy следует существующему lock/resolution contract;
  update не совмещается случайно с feature change.
- Package tests не полагаются на application singleton, bundle layout или
  signing environment без явного integration fixture.

Plan фиксирует manifest/project wiring, public API/visibility tests, module-level
test, consumer integration/build, dependency graph и app-shell composition. Все
commands и schemes/targets обнаруживаются. Tools/language version меняется
только после проверки всех consumers и CI matrix.

`deviation` от isolation допустим только в existing/discovered non-application
unit из adapter list, при точном repository constraint, typed protocol/API seam
уже сейчас и objective migration trigger. App target никогда не является
deviation. Малый размер репозитория, скорость изменения или существующий
app-target monolith сами по себе не достаточны. Одновременно запрещён
package/target на каждую папку, class
или layer: tiny one-consumer local behavior остаётся cohesive без physical split,
если split не улучшает ownership, testability, visibility или reuse.
