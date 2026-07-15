# Simulator execution

Simulator — ограниченный runtime resource, а не доказательство всех device
характеристик. Доступные runtimes/devices и команды обнаруживаются через текущий
Xcode/tooling; фиксированного pool или helper script не предполагается.

## Isolation

- Каждый параллельный run получает отдельный booted device и data namespace.
- Test plan описывает install/launch/reset policy, locale, appearance,
  permissions, status conditions и fixture source.
- Cleanup завершает app/test processes и освобождает только созданные текущим
  run resources; чужой booted simulator не удаляется.
- Device unavailable/boot failure даёт UNKNOWN с diagnostics, а не PASS.
- Screenshots, hierarchy, logs и result bundles сохраняются bounded и связаны с
  конкретной командой/runtime.

Simulator не воспроизводит performance, thermal, camera, push, background и
hardware behavior полностью. Для применимого риска plan указывает device/manual
evidence или явный residual risk. Parallelism вводится после измерения host
capacity; больше simulators может ухудшить стабильность.
