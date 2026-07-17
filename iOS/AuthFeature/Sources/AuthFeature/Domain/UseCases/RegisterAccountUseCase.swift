/// Регистрация нового аккаунта.
protocol RegisterAccountUseCase: Sendable {

    /// Возвращает сессионный секрет.
    func execute(email: String, password: String) async throws -> String
}
