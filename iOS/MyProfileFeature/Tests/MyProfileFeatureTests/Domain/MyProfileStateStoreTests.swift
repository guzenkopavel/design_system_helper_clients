@testable import MyProfileFeature
import XCTest

@MainActor
final class MyProfileStateStoreTests: XCTestCase {

    func test_reload_loadsProfileAndFullCount() async {
        let repository = StubProfileRepository(
            profile: MyProfileAccount(email: "pavel@example.com"),
            count: 3
        )
        let store = MyProfileStateStore(repository: repository)

        await store.reload()
        let calls = await repository.callCounts()

        XCTAssertEqual(store.state, .loaded(MyProfileSummary(email: "pavel@example.com", interviewCount: 3)))
        XCTAssertEqual(calls.profile, 1)
        XCTAssertEqual(calls.count, 1)
    }

    func test_reload_preventsDuplicateActiveRequest() async {
        let repository = StubProfileRepository(
            profile: MyProfileAccount(email: "pavel@example.com"),
            count: 1,
            delayNanoseconds: 50_000_000
        )
        let store = MyProfileStateStore(repository: repository)

        async let first: Void = store.reload()
        async let second: Void = store.reload()
        _ = await (first, second)
        let calls = await repository.callCounts()

        XCTAssertEqual(store.state, .loaded(MyProfileSummary(email: "pavel@example.com", interviewCount: 1)))
        XCTAssertEqual(calls.profile, 1)
    }

    func test_cancelLoadingPreventsStaleUpdate() async {
        let repository = StubProfileRepository(
            profile: MyProfileAccount(email: "pavel@example.com"),
            count: 1,
            delayNanoseconds: 50_000_000
        )
        let store = MyProfileStateStore(repository: repository)

        let task = Task {
            await store.reload()
        }
        try? await Task.sleep(nanoseconds: 5_000_000)
        store.cancelLoading()
        await task.value

        XCTAssertEqual(store.state, .idle)
    }

    func test_invalidSessionClearsVisibleProfileDataAndRecovers() async {
        let repository = StubProfileRepository(error: MyProfileFeatureError.invalidSession)
        var recoveryCallCount = 0
        let store = MyProfileStateStore(repository: repository) {
            recoveryCallCount += 1
        }

        await store.reload()

        XCTAssertEqual(store.state, .invalidSession)
        XCTAssertEqual(recoveryCallCount, 1)
    }

    func test_logoutFailureKeepsLoadedProfile() async {
        let summary = MyProfileSummary(email: "pavel@example.com", interviewCount: 2)
        let repository = StubProfileRepository(logoutError: MyProfileFeatureError.backend)
        let store = MyProfileStateStore(repository: repository, initialState: .loaded(summary))

        await store.logout()

        XCTAssertEqual(store.state, .logoutFailed(summary, message: "Не удалось выйти"))
    }
}

private actor StubProfileRepository: MyProfileRepository {

    private let profile: MyProfileAccount
    private let count: Int
    private let error: MyProfileFeatureError?
    private let logoutError: MyProfileFeatureError?
    private let delayNanoseconds: UInt64
    private(set) var fetchProfileCallCount = 0
    private(set) var fetchCountCallCount = 0

    init(
        profile: MyProfileAccount = MyProfileAccount(email: "profile@example.com"),
        count: Int = 0,
        error: MyProfileFeatureError? = nil,
        logoutError: MyProfileFeatureError? = nil,
        delayNanoseconds: UInt64 = 0
    ) {
        self.profile = profile
        self.count = count
        self.error = error
        self.logoutError = logoutError
        self.delayNanoseconds = delayNanoseconds
    }

    func fetchProfile() async throws -> MyProfileAccount {
        fetchProfileCallCount += 1
        try await delayIfNeeded()
        if let error {
            throw error
        }
        return profile
    }

    func fetchInterviewCount() async throws -> Int {
        fetchCountCallCount += 1
        try await delayIfNeeded()
        if let error {
            throw error
        }
        return count
    }

    func logout() async throws {
        if let logoutError {
            throw logoutError
        }
    }

    private func delayIfNeeded() async throws {
        guard delayNanoseconds > 0 else { return }
        try await Task.sleep(nanoseconds: delayNanoseconds)
    }

    func callCounts() -> (profile: Int, count: Int) {
        (fetchProfileCallCount, fetchCountCallCount)
    }
}
