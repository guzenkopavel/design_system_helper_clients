/// Проверка существования аккаунта по почте.
protocol CheckEmailUseCase: Sendable {

    /// Возвращает ``true``, если почта занята (аккаунт существует).
    func execute(_ email: String) async throws -> Bool
}
