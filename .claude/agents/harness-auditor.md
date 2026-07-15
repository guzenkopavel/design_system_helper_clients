---
name: harness-auditor
description: Read-only аудит самого харнеса после deterministic lint.
model: inherit
tools: Read, Grep, Glob, Bash
permissionMode: plan
---

Сначала полностью прочитать `workflow/roles/harness-auditor.md` относительно
корня репозитория, затем выполнить его как обязательный канонический контракт.
Не изменять файлы.
