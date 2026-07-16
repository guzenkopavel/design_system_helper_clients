/// Регистрация нового аккаунта.
public protocol RegisterAccountUseCase: Sendable {

    /// Возвращает сессионный секрет.
    func execute(email: String, password: String) async throws -> String
}
