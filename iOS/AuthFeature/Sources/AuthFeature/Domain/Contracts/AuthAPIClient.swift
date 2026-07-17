/// Контракт API-клиента auth-операций.
protocol AuthAPIClient: Sendable {

    func checkEmail(_ email: String) async throws -> Bool
    func login(email: String, password: String) async throws -> String
    func register(email: String, password: String) async throws -> String
    func checkSession(token: String) async throws -> Bool
}
