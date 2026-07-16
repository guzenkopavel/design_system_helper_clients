import Foundation

/// Конфигурация auth — адрес API бэкенда.
/// Throwing-инициализатор отклоняет не-https адреса.
public struct AuthConfiguration: Sendable {

    public let apiBaseURL: URL

    public init(apiBaseURL: URL) throws {
        guard apiBaseURL.scheme == "https" else {
            throw AuthError.invalidConfiguration
        }
        self.apiBaseURL = apiBaseURL
    }
}
