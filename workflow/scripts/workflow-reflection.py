#!/usr/bin/env python3
"""Print a focused reflection checklist without repository-specific dependencies."""

from __future__ import annotations

import argparse

CHECKS = {
    "propose": (
        "Какое path/source утверждение не подтверждено фактическим файлом?",
        "Не скопированы ли shared REQ/AC вместо ссылок на IDs?",
        "Какой product, system-design или iOS gate остался неявно пропущен?",
        "Какое архитектурное решение зависит от open question?",
        "Достаточно ли verification mapping для каждого shared и IOS AC?",
    ),
    "plan": (
        "Есть ли задача более одного layer или более 2 ideal dev-days?",
        "Есть ли скрытая dependency, отсутствующая в DAG?",
        "Может ли исполнитель выполнить каждую задачу без перечитывания чата?",
        "Не объявлен ли proposed greenfield path существующим?",
        "Есть ли UI task без simulator, accessibility или design-system checks?",
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=sorted(CHECKS))
    args = parser.parse_args()
    print(f"Reflection — {args.phase}")
    for index, check in enumerate(CHECKS[args.phase], 1):
        print(f"{index}. {check}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
