import Foundation

/// Источник времени для отсчёта Retry-After.
public protocol TimeProvider: Sendable {

    func now() -> Date
}
