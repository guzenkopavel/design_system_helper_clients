import Foundation

@MainActor
public struct AuthFeatureFactory: Sendable {

    public enum StubScenario: Sendable {
        case signedOut
        case active
        case invalidSession
    }

    public init() {}

    public func makeSessionModel(configuration: AuthConfiguration) -> AuthSessionModel {
        let client = DefaultAuthAPIClient(configuration: configuration)
        let store = KeychainSessionSecretStore()
        let checkSession = DefaultCheckSessionUseCase(client: client, store: store)
        let checkEmail = DefaultCheckEmailUseCase(client: client)
        let logIn = DefaultLogInUseCase(client: client, store: store)
        let registerAccount = DefaultRegisterAccountUseCase(client: client, store: store)
        let timeProvider = SystemTimeProvider()

        return AuthSessionModel(
            checkSession: checkSession,
            store: store,
            makeFlowViewModel: { sessionModel in
                AuthFlowViewModel(
                    checkEmail: checkEmail,
                    logIn: logIn,
                    registerAccount: registerAccount,
                    timeProvider: timeProvider,
                    completeAuthentication: {
                        sessionModel.completeAuthentication()
                    }
                )
            }
        )
    }

    func makeSessionModel(
        initialState: SessionState = .checking,
        checkSession: CheckSessionUseCase,
        store: SessionSecretStore,
        makeFlowViewModel: @escaping @MainActor @Sendable (AuthSessionModel) -> AuthFlowViewModel = { _ in
            preconditionFailure("AuthSessionModel requires a flow view model builder")
        }
    ) -> AuthSessionModel {
        AuthSessionModel(
            initialState: initialState,
            checkSession: checkSession,
            store: store,
            makeFlowViewModel: makeFlowViewModel
        )
    }

    public func makeStubSessionModel(scenario: StubScenario = .signedOut) -> AuthSessionModel {
        let store = StubSessionSecretStore(initialSecret: scenario.initialSecret)
        let checkSession = StubCheckSessionUseCase(result: scenario.startResult)
        let checkEmail = StubCheckEmailUseCase()
        let logIn = StubLogInUseCase()
        let registerAccount = StubRegisterAccountUseCase()
        let timeProvider = SystemTimeProvider()

        return AuthSessionModel(
            checkSession: checkSession,
            store: store,
            makeFlowViewModel: { sessionModel in
                AuthFlowViewModel(
                    checkEmail: checkEmail,
                    logIn: logIn,
                    registerAccount: registerAccount,
                    timeProvider: timeProvider,
                    completeAuthentication: {
                        sessionModel.completeAuthentication()
                    }
                )
            }
        )
    }

    func makeStubSessionModel(
        initialSecret: String? = nil,
        startResult: StubStartResult = .missingSession
    ) -> AuthSessionModel {
        let store = StubSessionSecretStore(initialSecret: initialSecret)
        let checkSession = StubCheckSessionUseCase(result: startResult)
        return AuthSessionModel(checkSession: checkSession, store: store)
    }
}

private extension AuthFeatureFactory.StubScenario {

    var initialSecret: String? {
        switch self {
        case .signedOut:
            return nil
        case .active:
            return "stub-active-session"
        case .invalidSession:
            return "stub-expired-session"
        }
    }

    var startResult: StubStartResult {
        switch self {
        case .signedOut:
            return .missingSession
        case .active:
            return .validSession
        case .invalidSession:
            return .invalidSession
        }
    }
}

private struct SystemTimeProvider: TimeProvider {

    func now() -> Date {
        Date()
    }
}

enum StubStartResult: Sendable {
    case missingSession
    case validSession
    case invalidSession
    case failure
}

private struct StubCheckEmailUseCase: CheckEmailUseCase {

    func execute(_ email: String) async throws -> Bool {
        let normalizedEmail = email.lowercased()
        return !normalizedEmail.contains("new")
            && !normalizedEmail.contains("register")
            && !normalizedEmail.contains("signup")
    }
}

private struct StubLogInUseCase: LogInUseCase {

    func execute(email: String, password: String) async throws -> String {
        guard password.count >= 6 else {
            throw AuthError.invalidInput(message: "Пароль должен содержать не менее 6 символов")
        }
        return "stub-login-session"
    }
}

private struct StubRegisterAccountUseCase: RegisterAccountUseCase {

    func execute(email: String, password: String) async throws -> String {
        guard password.count >= 6 else {
            throw AuthError.invalidInput(message: "Пароль должен содержать не менее 6 символов")
        }
        return "stub-register-session"
    }
}

private final class StubCheckSessionUseCase: CheckSessionUseCase, @unchecked Sendable {

    private let result: StubStartResult

    init(result: StubStartResult) {
        self.result = result
    }

    func execute() async throws -> Bool {
        switch result {
        case .missingSession:
            return false
        case .validSession:
            return true
        case .invalidSession:
            throw AuthError.sessionInvalid
        case .failure:
            throw AuthError.offline
        }
    }
}

private final class StubSessionSecretStore: SessionSecretStore, @unchecked Sendable {

    private var secret: String?

    init(initialSecret: String?) {
        self.secret = initialSecret
    }

    func save(_ secret: String) async throws {
        self.secret = secret
    }

    func load() async throws -> String? {
        secret
    }

    func remove() async throws {
        secret = nil
    }
}
