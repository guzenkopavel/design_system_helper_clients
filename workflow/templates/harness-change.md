# Harness Change Plan — <short-name>

## Intake

- **Тип:** rule | phase | profile | skill | command | agent | hook | script | template | doc
- **Операция:** add | modify | remove | move
- **Зачем:** <какой outcome или failure mode>
- **Scope:** common | ios | android | cross-platform

## Locate

- **Затронутый flow:** <ссылка на process map>
- **Канонический владелец:** <путь>
- **Placement:** canonical | adapter · common | ios | android
- **SSOT-проверка:** <что найдено по назначению и синонимам>
- [ ] Релевантные scripts/skills/roles перечислены и просмотрены

## Forbidden

- **Зависимости:** <кто ссылается на владельца>
- **Инварианты:** single-writer · no-commit · SSOT · platform isolation · …

## Rigidity

- **Hard change:** да | нет
- **Test evidence:** `workflow/test-evidence/<name>.md` | skip: <причина>

## Wiring cascade

- [ ] process map
- [ ] agent roster
- [ ] portable skill metadata и Codex/Claude Code/Cursor/OpenCode adapters
- [ ] workflow index
- [ ] root/platform AGENTS при изменении entry point
- [ ] test evidence для hard change

## Platform evidence

- [ ] iOS: passed | not affected + evidence
- [ ] Android: passed | not affected + evidence

## Acceptance

- [ ] `harness-lint.py`: grade A
- [ ] `harness-auditor`: CLEAN
- [ ] Нет orphan-файлов и битых ссылок
