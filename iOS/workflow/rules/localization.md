# iOS localization

User-visible strings must use the localization mechanism already present in the
client; discover keys, tables and generation tools before editing. Avoid string
concatenation that prevents grammatical reordering. Verification covers missing
keys, interpolation/plural forms, expanded text layout and at least one
non-default locale when localization is in task scope.

Locale-sensitive presentation использует Foundation formatters с явно выбранной
locale/calendar/time zone policy. Machine identifiers, protocol keys и stable
storage values не нормализуются через пользовательскую locale; для них
применяется контрактно заданное, locale-independent сравнение. Пользовательский
поиск/casing, напротив, обязан учитывать актуальную locale и язык данных.

- Plural/select forms хранятся в поддерживаемом механизмом проекта формате.
- Interpolation сохраняет типы и порядок аргументов; предложения не собираются
  конкатенацией fragments.
- Right-to-left layout не фиксируется ручным left/right, если семантика leading/
  trailing корректна.
- Date/number/unit output не проверяется по одному hard-coded English string.
- Новые keys имеют ownership и fallback согласно обнаруженной конфигурации.

Актуальное SDK behavior и generated localization API подтверждаются project
settings/docs; не предполагать конкретную версию toolchain.
