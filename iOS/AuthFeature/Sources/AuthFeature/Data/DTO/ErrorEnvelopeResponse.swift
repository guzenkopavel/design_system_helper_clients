import Foundation

/// Конверт ошибок бэкенда: код, сообщение, повторяемость, трассировка.
internal struct ErrorEnvelopeResponse: Decodable {
    let error: ErrorDetail

    internal struct ErrorDetail: Decodable {
        let code: String
        let message: String
        let retryable: Bool
        let traceId: String?
    }
}
