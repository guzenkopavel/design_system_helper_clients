/// Состояние сессии.
public enum SessionState: Sendable {

    /// Причина завершения сессии для маршрутизации истечения.
    public enum EndReason: Sendable {
        case sessionInvalid
    }

    case checking
    case signedOut(reason: EndReason?)
    case active
}
