# Profiling

Выбрать инструмент по hypothesis: time profile, points of interest, allocations,
leaks, network, energy, hangs или organizer metrics. Название/наличие инструмента
подтверждается установленным toolchain.

Trace содержит scenario markers, device/runtime, build configuration, start/end
условия и commit/worktree identity при delivery scope. Сначала читать dominant
stack/interval, затем сверять с source и повторять focused measurement.

Profiler overhead и debug instrumentation отмечаются. Скриншот графика без raw
trace/summary и воспроизводимого scenario — слабое evidence. После изменения
обязательно повторить тем же методом и проверить functional regressions.
