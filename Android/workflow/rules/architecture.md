# Android architecture

Официальные [guidance](https://developer.android.com/topic/architecture) и
[recommendations](https://developer.android.com/topic/architecture/recommendations)
задают сильный адаптируемый default: UI/Data separation, repository/data-source
boundary, SSOT, UDF, immutable UI state и lifecycle-aware collection. Это не
универсальная форма для каждого проекта: отклонение допустимо с evidence,
rationale и trade-offs. Domain/use cases условны. Screen state holder обычно не
удерживает Activity/Context/Resources, а app components обычно не являются data
owners; существующая доказанная архитектура может выбрать иной контракт.

Physical modularity задаёт
[`architecture/modularization.md`](architecture/modularization.md): cohesive
feature/data/network/storage/UI capabilities — strong-default modules, а
application module остаётся composition-only. Folders/layers не удовлетворяют
этому boundary; deviation требует existing/discovered library unit, sealed typed
seam и migration trigger и никогда не разрешает application module ownership.
