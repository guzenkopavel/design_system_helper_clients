# Android propose/plan/implement — RED/GREEN

## RED baseline

До изменения `find-platform-context.py --platform android --phase propose` и
`validate-platform-change.py` в modes propose/plan/implement возвращали `NOT
IMPLEMENTED`. Отсутствовали `Android/workflow/platform-contract.json`, phase
addenda и architecture/kotlin-style/gradle-build rules.

## GREEN

- Android adapter имеет exact ordered capabilities `propose, plan, implement`.
- Propose/Plan/Implement profiles и applicable union содержат только Android/common rules.
- Android Verify, capture, verify baseline и implementation archive fail closed.
- Compose/multiplatform/tooling не выбираются неявно.
- Compose требует явный UI scope; architecture guidance оформлена как strong
  adaptable default, а не universal HARD.
- iOS сохраняет все пять capabilities; product archive остаётся отдельным shared flow.

Команды: `python3 workflow/scripts/validate-platform-change.py --self-test`,
`find-platform-context.py --platform android --feature probe --phase propose
--scope application`, все script self-tests, `harness-lint.py --warn-as-error`,
`py_compile`, `bash -n`, `git diff --check` и skill quick validation — PASS.
`harness-lint.py --self-test` отдельно мутирует Android catalog/profile,
disabled Verify profile, Compose dependency и fixed source assumptions — RED.
