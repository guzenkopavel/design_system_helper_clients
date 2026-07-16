import Foundation

/// Доменные ошибки auth.
public enum AuthError: Error, Sendable {

    case invalidInput(message: String)
    case emailAlreadyRegistered
    case serverValidation(message: String)
    case rateLimited(retryAfter: Date)
    case offline
    case sessionInvalid
    case backendFailure(traceID: String?)
    case invalidConfiguration
}
