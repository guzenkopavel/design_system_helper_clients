# Android addendum: Propose

Использовать adapter root/prefix `AND`, обнаружить реальные modules/Gradle/KMP
boundaries. Разделение UI/Data — strong default из official recommendations, а
не универсальный запрет: альтернатива допустима с repository evidence, rationale
и trade-offs. Domain, Compose и multiplatform выбираются только по evidence.
Boundary review выполняет `android-package-boundary-guard`.
Common modularity и Android modularization rule применяются всегда, а не только
при optional `module` scope. Independent feature/data/network/storage/reusable
UI capability по strong default получает обнаруженный Gradle Android/Kotlin
library module; application module оставляет entry/root navigation/lifecycle/DI/config/
resources и composition. `isolated` добавляет `module`; structured missing или
`BLOCK` guard verdict блокирует design gate. Deviation допускается только в
existing/discovered library module и никогда в application module.
Для product-backed `ui` после specification writer вызвать
`android-ux-designer`: он пишет только READY `platform-ux.md`, подтверждает
Material 3 и условность M3 Expressive/dynamic color до architecture.
