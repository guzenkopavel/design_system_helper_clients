# Android addendum: Implementation Archive

Использовать общий [`archive`](../../../workflow/phases/archive.md) только после
fresh Android verification fingerprint и успешного terminal validator.
Implementation package переносится из Android adapter active namespace в его
`archive_namespace`; exact destination, receipt и tombstone формирует общий
collision-safe algorithm.

Всегда выполнить dry-run до apply. Не допускать overwrite, force, stale
fingerprint или неполный receipt. При ошибке общий rollback сохраняет pre-call
state. Shared product package и product archive flow не изменять и не
дублировать общий archive algorithm в этом addendum.
