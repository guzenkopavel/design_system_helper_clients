/// Проверка валидности серверной сессии.
public protocol CheckSessionUseCase: Sendable {

    /// Возвращает ``true``, если сессия валидна.
    func execute() async throws -> Bool
}
