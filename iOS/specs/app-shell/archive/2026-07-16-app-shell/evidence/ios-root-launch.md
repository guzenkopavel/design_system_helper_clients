# Evidence IOS-AC-1 — root launch

Статус: PASS.

`xcodebuild test` собрал и запустил app/test targets на simulator
`iPhone 17 Pro`, iOS 26.5. Launch tests из `SysDevScenUITestsLaunchTests`
прошли в light/dark и orientation configurations; focused UI tests запустили
bundle `none.SysDevScen` и нашли app-shell navigation.

Дополнительный `simctl launch` вернул процесс для `none.SysDevScen`, после чего
screenshots подтвердили текущую root surface.
