# Test execution

Команды тестирования извлекаются из реальной конфигурации проекта, CI и package
manifests. Нельзя придумывать build unit, configuration, runtime destination или
test selection.
Greenfield-команда помечается provisional и подтверждается до terminal verify.

## Порядок запуска

1. Самый узкий deterministic test для текущего поведения.
2. Тесты изменённого модуля и его прямых dependents.
3. Интеграционные/UI/runtime проверки, если затронута соответствующая граница.
4. Более широкий regression suite, когда это требует risk profile или release
   gate.

Nontrivial команда запускается через
[`test-watchdog.sh`](../scripts/test-watchdog.sh): указываются максимальное
время, stall budget и output cap. Override допустим только с записанной причиной
и новым конечным лимитом. Watchdog не превращает timeout/stall в PASS.

## Evidence

Сохраняются точная команда, окружение/устройство, exit status, длительность,
проверенный контракт и ссылка на полный log или compact failure excerpt.
Повторный запуск только упавшего теста не стирает исходный failure.

Flaky результат классифицируется как FAIL или UNKNOWN согласно
[`verification-evidence.md`](verification-evidence.md), пока причина не устранена
или риск явно не принят человеком. Запрещено бесконечно повторять тест до green.
