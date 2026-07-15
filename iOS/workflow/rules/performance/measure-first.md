# Measure first

1. Сформулировать пользовательский symptom и metric.
2. Зафиксировать reproducible scenario, environment и baseline distribution.
3. Получить trace/profile и найти dominant cost, не guessing hotspot.
4. Изменить одну hypothesis-controlled переменную.
5. Повторить одинаковый scenario достаточное число раз и сравнить distribution.
6. Проверить correctness, memory/energy/network trade-offs и regression scope.

Один лучший run не является evidence. Среднее без variance/percentiles может
скрывать tail. Threshold берётся из product SLO или измеренного baseline с
обоснованным budget; универсальных миллисекундных лимитов нет.
