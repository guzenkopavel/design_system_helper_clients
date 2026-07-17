/// Вход существующего аккаунта.
protocol LogInUseCase: Sendable {

    /// Возвращает сессионный секрет.
    func execute(email: String, password: String) async throws -> String
}
