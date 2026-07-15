# System design review

Полный review обязателен для нового модуля/package, migration, cross-boundary
интеграции, security/privacy, concurrency/state machine и трудно обратимой
зависимости.

Перед `specified` проверить:

- landscape и источники истины;
- primary + secondary requirements;
- открытые вопросы и defended decisions;
- applicable mobile challenges;
- architecture/data/control flow и failure exits;
- migration/rollback/security/privacy;
- verification mapping;
- HDD ordering, one-layer work items и range estimate.

Непройденный применимый пункт — blocker либо явный `N/A` с доказуемой причиной.
