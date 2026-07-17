# Verification — my-profile / Android / my-profile

## Strategy

Проверка стартует как pending, потому что фаза propose не создаёт production code и пока не имеет runtime evidence для Android. Следующая фаза должна разложить покрытие на границу модуля, repository для pagination/logout, держатель состояния, семантику Compose UI, интеграцию оболочки, ресурсы локализации и доказательства нативного внешнего вида; каждая будущая проверка получит отдельное доказательство. Runtime проверки выполняются только на обнаруженном emulator/device с finite watchdog.

## Modularity verification

- Dependency graph: pending
- Public API and visibility: pending
- Module-level tests: pending
- Consumer integration and build: pending
- App-shell allowlist: pending

## Native UX verification

Native UX проверяется через внешний вид Material 3, light/dark/increased contrast, TalkBack semantics, масштаб текста, краткую обратную связь, адаптацию устройства и fallback behavior; эти проверки нужны для доступности и паритета Android на реальном интерфейсе. До реализации все нативные obligations остаются `pending`.

## Native obligation coverage

| Obligation ID | Observation record | Status |
|---|---|---|
| NATIVE-APPEARANCE | pending | pending |
| NATIVE-LIGHT | pending | pending |
| NATIVE-DARK | pending | pending |
| NATIVE-INCREASED-CONTRAST | pending | pending |
| NATIVE-ASSISTIVE-SEMANTICS | pending | pending |
| NATIVE-TEXT-SCALING | pending | pending |
| NATIVE-MOTION | pending | pending |
| NATIVE-DEVICE-ADAPTATION | pending | pending |
| NATIVE-AVAILABILITY-FALLBACK | pending | pending |

## Contract matrix

| Contract ID | Dimension | Method | Evidence | Status |
|---|---|---|---|---|
| REQ-1 | Проверка контракта REQ-1 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| REQ-2 | Проверка контракта REQ-2 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| REQ-3 | Проверка контракта REQ-3 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| REQ-4 | Проверка контракта REQ-4 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| REQ-5 | Проверка контракта REQ-5 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| REQ-6 | Проверка контракта REQ-6 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| REQ-7 | Проверка контракта REQ-7 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| REQ-8 | Проверка контракта REQ-8 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| REQ-9 | Проверка контракта REQ-9 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| REQ-10 | Проверка контракта REQ-10 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AC-1 | Проверка контракта AC-1 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AC-2 | Проверка контракта AC-2 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AC-3 | Проверка контракта AC-3 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AC-4 | Проверка контракта AC-4 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AC-5 | Проверка контракта AC-5 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AC-6 | Проверка контракта AC-6 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AC-7 | Проверка контракта AC-7 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AC-8 | Проверка контракта AC-8 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AC-9 | Проверка контракта AC-9 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AC-10 | Проверка контракта AC-10 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AC-11 | Проверка контракта AC-11 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AC-12 | Проверка контракта AC-12 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AC-13 | Проверка контракта AC-13 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AC-14 | Проверка контракта AC-14 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AC-15 | Проверка контракта AC-15 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AC-16 | Проверка контракта AC-16 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AC-17 | Проверка контракта AC-17 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AC-18 | Проверка контракта AC-18 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-REQ-1 | Проверка контракта AND-REQ-1 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-REQ-2 | Проверка контракта AND-REQ-2 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-REQ-3 | Проверка контракта AND-REQ-3 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-REQ-4 | Проверка контракта AND-REQ-4 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-REQ-5 | Проверка контракта AND-REQ-5 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-REQ-6 | Проверка контракта AND-REQ-6 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-REQ-7 | Проверка контракта AND-REQ-7 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-REQ-8 | Проверка контракта AND-REQ-8 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-REQ-9 | Проверка контракта AND-REQ-9 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-REQ-10 | Проверка контракта AND-REQ-10 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-REQ-11 | Проверка контракта AND-REQ-11 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-REQ-12 | Проверка контракта AND-REQ-12 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-AC-1 | Проверка контракта AND-AC-1 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-AC-2 | Проверка контракта AND-AC-2 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-AC-3 | Проверка контракта AND-AC-3 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-AC-4 | Проверка контракта AND-AC-4 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-AC-5 | Проверка контракта AND-AC-5 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-AC-6 | Проверка контракта AND-AC-6 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-AC-7 | Проверка контракта AND-AC-7 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-AC-8 | Проверка контракта AND-AC-8 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-AC-9 | Проверка контракта AND-AC-9 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-AC-10 | Проверка контракта AND-AC-10 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-AC-11 | Проверка контракта AND-AC-11 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-AC-12 | Проверка контракта AND-AC-12 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-AC-13 | Проверка контракта AND-AC-13 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-AC-14 | Проверка контракта AND-AC-14 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
| AND-AC-15 | Проверка контракта AND-AC-15 | Будущая проверка покрывает этот контракт по утверждённой матрице Android и shared package. | pending | pending |
