---
name: propose
description: Создать platform implementation package при поддержанной propose capability.
---

# Propose

Полностью выполнить [`workflow/phases/propose.md`](../../../workflow/phases/propose.md).

1. Разобрать `$propose <platform> <feature> [--change <change-id>] [--tier quick|standard|extended] [--technical-only]`.
2. Потребовать platform/feature и strict kebab-case identity. Для нового цикла
   omitted change равен feature. Unsupported/unknown/unsafe/collision — blocker и
   ноль записей.
3. Применить product-backed либо доказанный technical-only intake.
4. По repository evidence выбрать adapter-defined engineering scopes, получить
   exact proposal rules через `find-platform-context.py --phase propose` и
   записать scopes + полный derived lifecycle union в meta/proposal.
5. Последовательно вызвать read-only discovery, spec/design writers и platform
   boundary guard.
6. Создать только пять файлов в
   adapter package root; не копировать shared REQ/AC.
7. Запустить validator с входной platform и `--mode propose`.
8. Сохранить `specified` только при green; иначе вернуть `draft`.

Manual-only. Не создавать plan, production code или commit.
