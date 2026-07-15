# UI test specification

Для каждого shared/IOS AC выбрать сценарий и разложить steps→actions/assertions.
Определить fixture/reset, selector priority, identifier gaps, subflow reuse и
simulator state. Каждый шаг покрыт либо исключён с причиной. Output хранится в
`verification.md` и соответствующей plan task, отдельный дублирующий product
scenario не создавать.

Спецификация фиксирует preconditions, controlled data, launch arguments/env,
action, observable assertion, cleanup и диагностические artifacts. Она не
придумывает automation framework: сначала обнаруживаются test targets и helpers.

Для ветвящегося flow перечисляются только contract-significant paths. Каждая
coordinate/index fallback помечается как риск с задачей на stable accessibility
identifier, если identifier находится в owned scope.
