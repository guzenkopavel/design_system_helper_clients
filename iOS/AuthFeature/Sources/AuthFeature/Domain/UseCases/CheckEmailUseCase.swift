/// Проверка существования аккаунта по почте.
public protocol CheckEmailUseCase: Sendable {

    /// Возвращает ``true``, если почта занята (аккаунт существует).
    func execute(_ email: String) async throws -> Bool
}
