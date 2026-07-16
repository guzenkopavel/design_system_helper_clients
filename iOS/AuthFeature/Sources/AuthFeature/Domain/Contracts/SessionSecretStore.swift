/// Контракт хранилища сессионного секрета.
public protocol SessionSecretStore: Sendable {

    func save(_ secret: String) async throws
    func load() async throws -> String?
    func remove() async throws
}
