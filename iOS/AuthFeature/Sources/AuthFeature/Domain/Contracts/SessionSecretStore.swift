/// Контракт хранилища сессионного секрета.
protocol SessionSecretStore: Sendable {

    func save(_ secret: String) async throws
    func load() async throws -> String?
    func remove() async throws
}
