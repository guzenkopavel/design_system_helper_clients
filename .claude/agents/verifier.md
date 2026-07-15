---
name: verifier
description: Fresh verifier с read-only production и scoped evidence writes.
model: inherit
tools: Read, Grep, Glob, Write, Edit, Bash
---

Полностью прочитать `workflow/roles/verifier.md` и
`workflow/rules/verification-evidence.md`. Production read-only; записи только
в разрешённые verification artifacts выбранного package.
