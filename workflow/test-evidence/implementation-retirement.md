# Implementation retirement evidence

## Задача

Нужно закрывать незавершённый platform package, который не может честно стать
`verified`, но уже владеет production Paths и блокирует новый superseding
change. Старый маршрут `archive implementation` требовал terminal evidence и
оставлял такие packages в active namespace.

## RED

Реальный pressure scenario на `iOS/user-profile-auth/user-profile-auth`:

```text
rtk python3 workflow/scripts/archive-change.py implementation --platform ios --feature user-profile-auth --change user-profile-auth
```

Результат: `BLOCKED`; обычный archive требует `verified`, `PASS` rows,
`verified_at` и `verification_state`. При этом:

```text
rtk python3 workflow/scripts/validate-platform-change.py --platform ios --feature user-profile-auth --change user-profile-auth --mode implement
```

Результат: `VALID (implement, iOS/user-profile-auth/user-profile-auth)`. Package
валиден как non-terminal implementation lane, но не может быть выведен из
active ownership штатным archive.

## GREEN

Добавлен явный путь:

```text
rtk python3 workflow/scripts/archive-change.py implementation --platform ios --feature user-profile-auth --change user-profile-auth --retire superseded
```

Результат: `DRY-RUN`; package будет перемещён в
`iOS/specs/user-profile-auth/archive/2026-07-17-user-profile-auth`,
`ARCHIVED.md` останется в active namespace, а
`iOS/specs/user-profile-auth/SPECIFICATION.md` не публикуется и не меняется.

## Pressure checks

```text
rtk python3 workflow/scripts/archive-change.py --self-test
```

Результат: `PASS`. Проверены:

- обычный verified archive не изменил поведение и публикует durable baseline;
- `--retire superseded|cancelled` принимает только non-terminal
  `specified|planned|implementing`;
- retirement rollback восстанавливает pre-call tree при fault injection;
- iOS и Android retirement сохраняют прежний `SPECIFICATION.md` byte-for-byte;
- retirement receipt валиден для tombstone classification, но не проходит как
  delivered `archived` disposition evidence;
- product active-reference scan принимает tombstones с verified archive receipt
  или retirement receipt, но по-прежнему блокирует partial/broken tombstones.

Дополнительно:

```text
rtk python3 workflow/scripts/validate-platform-change.py --self-test
```

Результат: pre-existing failure:
`ios registry-anchored v0 implement regression` из-за fixture path
`iOS/SysDevScen/SysDevScen/Preview\\ Content/Preview\\ Assets.xcassets`.
Новая implementation-retirement ветка не участвует в этом self-test; targeted
`user-profile-auth` implement validator проходит.

## Остаточные ограничения

Retirement receipt не является delivery proof. `archive product completed` и
platform disposition `archived` продолжают требовать verified implementation
archive receipt. Retirement только выводит non-terminal package из active
ownership и сохраняет историю.
