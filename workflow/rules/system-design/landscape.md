# Landscape

До требований построить компактный граф: actors → client surfaces → domain
entities → state owners → external contracts → persistence/analytics. Для каждой
связи отметить source of truth, direction и неизвестность.

Разделить требования:

- primary — основной value path;
- secondary — loading/error/empty/offline, accessibility, localization,
  analytics/privacy, deeplink/push, recovery и rollout.

Secondary — first-class scope, не «потом». Отдельно записать known unknowns,
unknown-unknown probes, вопросы product/design/backend и принятые решения.
