# Свежие наблюдения кода и нативные пробелы

- `AC-9`: `MyProfileView` блокирует logout только при `isLogoutLoading`;
  `historyFailed` формирует `isLogoutLoading = false`. UI-тест наблюдал ошибку
  истории и недоступное действие «Мои интервью».
- `AC-11`: `MyProfileStateStoreTests.test_logoutFailureKeepsLoadedProfile`
  прошёл; состояние возвращается в `logoutFailed` с прежним summary.
- `IOS-REQ-6` / `IOS-AC-8`: тесты пакета наблюдали полную пагинацию,
  единственную активную загрузку и запрет устаревшего обновления после отмены.
- `AC-1` / `IOS-AC-5`: UI automation наблюдала email и обе кнопки, но не
  фиксировала профильный символ и его геометрию, поэтому критерий целиком
  остаётся `UNKNOWN`.
- `AC-12`: iOS run не содержит свежего Android observation и не доказывает
  межклиентский паритет.
- `AC-13` / `AC-14`: source содержит accessibility labels/hints, но реальный
  VoiceOver order, traits и announcements не наблюдались.
- `AC-15`–`AC-18`: инспекция кода и тесты состояний не заменяют runtime
  layout/appearance evidence.

Все девять нативных обязательств остаются `UNKNOWN`: текущие тесты не
переключают настройки оформления и доступности и не сохраняют отдельные
наблюдения для всех сценариев из `platform-ux.md`.
