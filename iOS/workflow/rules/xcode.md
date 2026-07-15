# iOS Xcode integration

Discover existing projects, packages, targets, schemes and build settings before
changing wiring. Never invent names in tasks or commands. Keep generated files
under their owning generator, avoid unrelated project-file churn, and record the
exact build/test invocation plus destination evidence used for verification.

## Discovery checklist

- Найти `.xcodeproj`/`.xcworkspace`, package manifests, shared schemes, test
  plans, configurations и CI commands.
- Зафиксировать deployment target, Swift language mode, strict concurrency,
  signing и generated-source ownership для затронутого target.
- Отличить checked-in project metadata от generated; generator запускается
  только найденной документированной командой.
- Избегать массового UUID/order churn в project file и unrelated signing edits.
- Build destination выбирается из доступных runtimes/devices; имя не hard-code.

Build success подтверждает compilation/linking выбранной конфигурации, но не
runtime behavior. Warning suppression, `SWIFT_VERSION` и availability меняются
только в task scope с совместимостью для всех затронутых targets.
