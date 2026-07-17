/// Проверка валидности серверной сессии.
protocol CheckSessionUseCase: Sendable {

    /// Возвращает ``true``, если сессия валидна.
    func execute() async throws -> Bool
}
