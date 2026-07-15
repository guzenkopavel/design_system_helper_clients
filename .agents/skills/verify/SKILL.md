---
name: verify
description: Свежо проверить реализованный change-aware platform package и зафиксировать fingerprinted evidence. Использовать только по явному вызову verify с platform identity; iOS поддержан, Android блокируется до записей.
---

# Verify

Полностью выполнить [`workflow/phases/verify.md`](../../../workflow/phases/verify.md)
и [`verification-evidence.md`](../../../workflow/rules/verification-evidence.md).

Форма: `$verify <platform> <feature> [--change <change-id>]`. После fail-before-
write identity gate передать current contracts/code роли `verifier`. Она не
меняет production и пишет только scoped evidence. При `FAIL`/`UNKNOWN` сохранить
recovery meta/problems, детерминированно reopen напрямую затронутые tasks и весь
их transitive dependent closure, затем остаться в `implementing`; unmapped
contract требует plan repair. При exact PASS очистить
problems, выставить candidate `status: verified`, захватить state fingerprint и
запустить validator `--mode verify --change`.

Manual-only. Старое или writer-authored утверждение не является доказательством;
не коммитить.
