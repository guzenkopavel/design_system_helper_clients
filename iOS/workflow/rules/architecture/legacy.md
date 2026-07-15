# Existing and legacy fit

Не вводить универсальную legacy policy без evidence текущего клиента. Navigator
должен отличить active, deprecated и generated zones по call sites, project
membership и локальной документации. Новый behavior не добавлять в подтверждённо
deprecated branch. Если статус не доказан — записать open question, не считать
путь legacy по имени.

Migration design фиксирует current callers, coexistence period, source of truth,
data compatibility, rollback и критерий удаления. Adapter/anti-corruption layer
предпочтительнее распространения старой модели в новый domain.

Нельзя одновременно менять поведение и массово переписывать структуру без
characterization evidence. Deprecated API получает owner и removal trigger;
вечный wrapper без плана считается новой legacy. Generated code меняется через
его generator или явно документированный ownership path.
