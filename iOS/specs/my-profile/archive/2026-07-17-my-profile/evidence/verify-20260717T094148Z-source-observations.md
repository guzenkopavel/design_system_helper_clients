# Fresh verification: source observations

- `AC-9`: `MyProfileView` блокирует logout только при `isLogoutLoading`; `historyFailed` формирует `isLogoutLoading = false`. Фокусный UI-тест наблюдал history error и disabled «Мои интервью».
- `AC-11`: `MyProfileStateStoreTests.test_logoutFailureKeepsLoadedProfile` прошёл; state возвращается в `logoutFailed` с прежним summary.
- `IOS-REQ-6` / `IOS-AC-8`: package tests наблюдали полную пагинацию, single active reload и запрет stale update после cancellation.
- `AC-1` / `IOS-AC-5`: UI automation наблюдала email и обе кнопки, но не фиксировала profile symbol и его геометрию, поэтому критерий целиком остаётся `UNKNOWN`.
- `AC-12`: iOS run не содержит fresh Android observation и не доказывает cross-client parity.
- `AC-13` / `AC-14`: source содержит accessibility labels/hints, но реальный VoiceOver order, traits и announcements не наблюдались.
- `AC-15`–`AC-18`: source inspection и state tests не заменяют runtime layout/appearance evidence.
