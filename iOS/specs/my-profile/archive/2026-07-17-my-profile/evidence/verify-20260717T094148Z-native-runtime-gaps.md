# Fresh verification: native runtime gaps

Simulator `iPhone 17` с iOS `26.5` был доступен и focused profile UI suite прошёл, но текущие тесты не переключают appearance/accessibility settings и не сохраняют требуемые observations. Поэтому базовая appearance-строка не закрыта полностью из-за отсутствия loading/signing-out observation, а light, dark, increased contrast, VoiceOver, максимальный Dynamic Type, Reduce Motion, iPad и older-OS/Reduce Transparency fallback остаются `UNKNOWN`.

Отдельно SwiftPM сообщил, что `Localizable.ru.strings` не включён manifest как resource. Это не превращает нативные строки в `FAIL` без runtime localization scenario, но блокирует утверждение о проверенной packaged localization.
