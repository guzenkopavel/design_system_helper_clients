/// Причина завершения сессии для маршрутизации истечения.
public enum SessionEndReason: Sendable {

    case sessionInvalid
}

/// Состояние сессии.
public enum SessionState: Sendable {

    case checking
    case signedOut(reason: SessionEndReason?)
    case active
}
