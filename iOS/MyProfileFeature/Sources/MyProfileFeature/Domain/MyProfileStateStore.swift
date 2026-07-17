@MainActor
public final class MyProfileStateStore {

    public private(set) var state: MyProfileState

    private let repository: any MyProfileRepository
    private let recoverInvalidSession: @MainActor @Sendable () async -> Void
    private var generation = 0
    private var activeLoadGeneration: Int?
    private var isSigningOut = false

    public init(
        repository: any MyProfileRepository,
        initialState: MyProfileState = .idle,
        recoverInvalidSession: @escaping @MainActor @Sendable () async -> Void = {}
    ) {
        self.repository = repository
        self.state = initialState
        self.recoverInvalidSession = recoverInvalidSession
    }

    public func reload() async {
        guard activeLoadGeneration == nil else { return }

        generation += 1
        let currentGeneration = generation
        activeLoadGeneration = currentGeneration
        state = .loading

        do {
            let profile = try await repository.fetchProfile()
            try Task.checkCancellation()
            guard isCurrentLoad(currentGeneration) else { return }

            let count = try await repository.fetchInterviewCount()
            try Task.checkCancellation()
            guard isCurrentLoad(currentGeneration) else { return }

            state = .loaded(MyProfileSummary(email: profile.email, interviewCount: count))
        } catch is CancellationError {
            if isCurrentLoad(currentGeneration) {
                state = .idle
            }
        } catch MyProfileFeatureError.invalidSession {
            await handleInvalidSession(currentGeneration: currentGeneration)
        } catch MyProfileFeatureError.offline {
            if isCurrentLoad(currentGeneration) {
                state = .historyFailed(email: currentEmail, message: "Нет соединения")
            }
        } catch {
            if isCurrentLoad(currentGeneration) {
                state = .historyFailed(email: currentEmail, message: "Не удалось загрузить историю")
            }
        }

        if activeLoadGeneration == currentGeneration {
            activeLoadGeneration = nil
        }
    }

    public func cancelLoading() {
        guard activeLoadGeneration != nil else { return }
        generation += 1
        activeLoadGeneration = nil
        state = .idle
    }

    public func logout() async {
        guard !isSigningOut else { return }

        isSigningOut = true
        let previousSummary = loadedSummary
        state = .signingOut(previousSummary)

        do {
            try await repository.logout()
            state = .signedOut
        } catch MyProfileFeatureError.invalidSession {
            await recoverInvalidSession()
            state = .invalidSession
        } catch {
            if let previousSummary {
                state = .logoutFailed(previousSummary, message: "Не удалось выйти")
            } else {
                state = .idle
            }
        }

        isSigningOut = false
    }

    private var loadedSummary: MyProfileSummary? {
        switch state {
        case let .loaded(summary), let .logoutFailed(summary, _):
            return summary
        case let .signingOut(summary):
            return summary
        default:
            return nil
        }
    }

    private var currentEmail: String {
        loadedSummary?.email ?? ""
    }

    private func isCurrentLoad(_ value: Int) -> Bool {
        activeLoadGeneration == value
    }

    private func handleInvalidSession(currentGeneration: Int) async {
        guard isCurrentLoad(currentGeneration) else { return }
        state = .invalidSession
        await recoverInvalidSession()
    }
}
