import Foundation

/// Источник времени для отсчёта Retry-After.
protocol TimeProvider: Sendable {

    func now() -> Date
}
