# Bug investigation

Bug mode доказывает причину, но не меняет код.

1. Нормализовать symptom, expected behavior source и reproduction preconditions.
2. Найти entry point и восстановить current call-chain через layers/boundaries.
3. Зафиксировать facts отдельно от hypotheses.
4. Рассмотреть минимум две competing hypotheses, если cause не очевидна; для
   каждой указать supporting/refuting evidence.
5. Проверить state/lifecycle, navigation, cancellation/concurrency, storage,
   DI, mapping/localization и platform integration только по relevance.
6. Root cause объявлять confirmed только при reproduction либо эквивалентном
   current-code/runtime proof, который исключает конкурирующие причины.

Без proof вернуть top hypotheses, confidence и exact evidence needed. Не
добавлять diagnostic logs, flags или production instrumentation. Предложить
минимальную fix surface и lifecycle route, но не выполнять fix.
