# Android addendum: Propose

Использовать adapter root/prefix `AND`, обнаружить реальные modules/Gradle/KMP
boundaries. Разделение UI/Data — strong default из official recommendations, а
не универсальный запрет: альтернатива допустима с repository evidence, rationale
и trade-offs. Domain, Compose и multiplatform выбираются только по evidence.
Boundary review выполняет `android-package-boundary-guard`.
Для product-backed `ui` после specification writer вызвать
`android-ux-designer`: он пишет только READY `platform-ux.md`, подтверждает
Material 3 и условность M3 Expressive/dynamic color до architecture.
