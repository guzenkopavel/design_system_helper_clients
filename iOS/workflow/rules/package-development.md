# Swift package development

Сначала определить manifest, products, targets, supported platforms, tools
version, dependency graph и реальных consumers. Не предполагать, что package
standalone, binary-compatible или используется application target.

- Product/API surface минимален; implementation types остаются internal.
- Target dependencies ацикличны и направлены от policy к details через
  contracts.
- Resources объявлены в manifest и проверены через consumer-compatible access.
- Platform-specific code изолирован availability/conditional compilation с
  тестом каждой поддерживаемой ветви.
- Dependency version policy следует существующему lock/resolution contract;
  update не совмещается случайно с feature change.
- Package tests не полагаются на application singleton, bundle layout или
  signing environment без явного integration fixture.

Plan включает standalone package command и, если public contract меняется,
consumer integration build/test. Tools/language version меняется только после
проверки всех consumers и CI matrix.
