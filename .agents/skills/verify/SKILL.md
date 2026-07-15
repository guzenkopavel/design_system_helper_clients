---
name: verify
description: Свежо проверить реализованный change-aware platform package и зафиксировать fingerprinted evidence. Использовать только по явному вызову verify с platform identity; iOS поддержан, Android блокируется до записей.
---

# Verify

Полностью выполнить [`workflow/phases/verify.md`](../../../workflow/phases/verify.md)
и [`verification-evidence.md`](../../../workflow/rules/verification-evidence.md).

Форма: `$verify <platform> <feature> [--change <change-id>]`. После fail-before-
write identity gate захватить canonical verify scope baseline и удерживать
выданный SHA-256 token только у coordinator, затем передать
current contracts/code роли `verifier`. Она не
меняет production, независимо загружает exact verify profile + те же scopes,
строит method matrix и пишет только scoped evidence. Nontrivial tests/runtime/
performance запускаются через watchdog с finite budgets. При `FAIL`/`UNKNOWN` сохранить
recovery meta/problems, детерминированно reopen напрямую затронутые tasks и весь
их transitive dependent closure, затем остаться в `implementing`; unmapped
contract требует plan repair. При exact PASS очистить
problems, выставить candidate `status: verified`, захватить state fingerprint и
запустить validator `--mode verify --change`.

До coordinator recovery/terminal writes выполнить verify scope check с исходным
`--expected-sha256`: production,
tasks, plan, contracts, rules и pre-existing evidence должны совпасть с baseline.

Manual-only. Старое или writer-authored утверждение не является доказательством;
не коммитить.
