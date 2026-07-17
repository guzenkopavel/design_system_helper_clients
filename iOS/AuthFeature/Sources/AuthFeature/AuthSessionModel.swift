import Combine
import Foundation

@MainActor
public final class AuthSessionModel: ObservableObject {

    @Published public private(set) var state: SessionState

    private let checkSession: CheckSessionUseCase
    private let store: SessionSecretStore
    private let makeFlowViewModel: @MainActor @Sendable (AuthSessionModel) -> AuthFlowViewModel
    private var didStart = false

    init(
        initialState: SessionState = .checking,
        checkSession: CheckSessionUseCase,
        store: SessionSecretStore,
        makeFlowViewModel: @escaping @MainActor @Sendable (AuthSessionModel) -> AuthFlowViewModel = { _ in
            preconditionFailure("AuthSessionModel requires a flow view model builder")
        }
    ) {
        self.state = initialState
        self.checkSession = checkSession
        self.store = store
        self.makeFlowViewModel = makeFlowViewModel
    }

    public func start() async {
        guard !didStart else { return }
        didStart = true

        do {
            state = try await checkSession.execute()
                ? .active
                : .signedOut(reason: nil)
        } catch AuthError.sessionInvalid {
            try? await store.remove()
            state = .signedOut(reason: .sessionInvalid)
        } catch {
            state = .signedOut(reason: nil)
        }
    }

    public func completeAuthentication() {
        state = .active
    }

    public func invalidateSession(reason: SessionState.EndReason = .sessionInvalid) async {
        try? await store.remove()
        state = .signedOut(reason: reason)
    }

    func makeAuthFlowViewModel() -> AuthFlowViewModel {
        makeFlowViewModel(self)
    }
}
