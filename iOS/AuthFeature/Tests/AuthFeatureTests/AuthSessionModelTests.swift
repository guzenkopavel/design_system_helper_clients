@testable import AuthFeature
import XCTest

@MainActor
final class AuthSessionModelTests: XCTestCase {

    func test_start_whenCalledTwice_checksSessionOnce() async {
        let checkSession = CountingCheckSessionUseCase(result: .success(true))
        let store = RecordingSessionSecretStore(initial: "token")
        let model = AuthSessionModel(checkSession: checkSession, store: store)

        await model.start()
        await model.start()

        XCTAssertEqual(checkSession.callCount, 1)
        XCTAssertActive(model.state)
    }

    func test_start_withValidSession_setsActive() async {
        let model = AuthSessionModel(
            checkSession: CountingCheckSessionUseCase(result: .success(true)),
            store: RecordingSessionSecretStore(initial: "token")
        )

        await model.start()

        XCTAssertActive(model.state)
    }

    func test_start_withMissingSession_setsSignedOutWithoutReason() async {
        let model = AuthSessionModel(
            checkSession: CountingCheckSessionUseCase(result: .success(false)),
            store: RecordingSessionSecretStore()
        )

        await model.start()

        XCTAssertSignedOut(model.state, reason: nil)
    }

    func test_start_withInvalidSession_clearsSecretAndSetsInvalidReason() async {
        let store = RecordingSessionSecretStore(initial: "expired")
        let model = AuthSessionModel(
            checkSession: CountingCheckSessionUseCase(result: .failure(AuthError.sessionInvalid)),
            store: store
        )

        await model.start()

        let storedSecret = try? await store.load()
        XCTAssertNil(storedSecret)
        XCTAssertSignedOut(model.state, reason: .sessionInvalid)
    }

    func test_completeAuthentication_setsActive() {
        let model = AuthSessionModel(
            checkSession: CountingCheckSessionUseCase(result: .success(false)),
            store: RecordingSessionSecretStore()
        )

        model.completeAuthentication()

        XCTAssertActive(model.state)
    }

    func test_invalidateSession_clearsSecretAndSetsReason() async {
        let store = RecordingSessionSecretStore(initial: "token")
        let model = AuthSessionModel(
            checkSession: CountingCheckSessionUseCase(result: .success(true)),
            store: store
        )

        await model.invalidateSession(reason: .sessionInvalid)

        let storedSecret = try? await store.load()
        XCTAssertNil(storedSecret)
        XCTAssertSignedOut(model.state, reason: .sessionInvalid)
    }
}

private final class CountingCheckSessionUseCase: CheckSessionUseCase, @unchecked Sendable {

    enum Result: Sendable {
        case success(Bool)
        case failure(AuthError)
    }

    private let result: Result
    private(set) var callCount = 0

    init(result: Result) {
        self.result = result
    }

    func execute() async throws -> Bool {
        callCount += 1
        switch result {
        case .success(let value):
            return value
        case .failure(let error):
            throw error
        }
    }
}

private final class RecordingSessionSecretStore: SessionSecretStore, @unchecked Sendable {

    private var secret: String?

    init(initial: String? = nil) {
        self.secret = initial
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

private func XCTAssertActive(
    _ state: SessionState,
    file: StaticString = #filePath,
    line: UInt = #line
) {
    guard case .active = state else {
        return XCTFail("Expected active state, got \(state)", file: file, line: line)
    }
}

private func XCTAssertSignedOut(
    _ state: SessionState,
    reason expectedReason: SessionState.EndReason?,
    file: StaticString = #filePath,
    line: UInt = #line
) {
    guard case .signedOut(let reason) = state else {
        return XCTFail("Expected signedOut state, got \(state)", file: file, line: line)
    }

    switch (reason, expectedReason) {
    case (.none, .none), (.sessionInvalid?, .sessionInvalid?):
        return
    default:
        XCTFail("Expected reason \(String(describing: expectedReason)), got \(String(describing: reason))", file: file, line: line)
    }
}
