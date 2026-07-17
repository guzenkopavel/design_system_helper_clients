@testable import AuthFeature
import XCTest

@MainActor
final class AuthFeatureFactoryTests: XCTestCase {

    func test_makeSessionModel_buildsCheckingLiveModel() throws {
        let configuration = try AuthConfiguration(
            apiBaseURL: XCTUnwrap(URL(string: "https://89.125.1.21.nip.io"))
        )

        let model = AuthFeatureFactory().makeSessionModel(configuration: configuration)

        XCTAssertChecking(model.state)
    }

    func test_makeSessionModel_withInjectedDependencies_buildsDeterministicModel() async {
        let model = AuthFeatureFactory().makeSessionModel(
            checkSession: FactoryCheckSessionUseCase(result: true),
            store: FactorySessionSecretStore(initial: "token")
        )

        await model.start()

        XCTAssertFactoryActive(model.state)
    }

    func test_makeStubSessionModel_supportsValidSessionScenario() async {
        let model = AuthFeatureFactory().makeStubSessionModel(
            initialSecret: "token",
            startResult: .validSession
        )

        await model.start()

        XCTAssertFactoryActive(model.state)
    }

    func test_makeStubSessionModel_supportsInvalidSessionScenario() async {
        let model = AuthFeatureFactory().makeStubSessionModel(
            initialSecret: "expired",
            startResult: .invalidSession
        )

        await model.start()

        XCTAssertFactorySignedOut(model.state, reason: .sessionInvalid)
    }

    func test_publicTopLevelContract_containsOnlyApprovedTypes() throws {
        let sourceRoot = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .appendingPathComponent("Sources/AuthFeature")
        let allSwiftFiles = try sourceRoot.recursiveSwiftFiles()
        let publicDeclarations = try allSwiftFiles.flatMap { file -> [String] in
            let contents = try String(contentsOf: file)
            return contents
                .split(separator: "\n")
                .compactMap { line -> String? in
                    guard line.hasPrefix("public ") else { return nil }
                    let parts = line.split(separator: " ")
                    guard parts.count >= 3 else { return nil }
                    if parts[1] == "final", parts.count >= 4 {
                        return String(parts[3].split(separator: ":")[0])
                    }
                    if ["struct", "enum", "actor", "protocol", "class"].contains(parts[1]) {
                        return String(parts[2].split(separator: ":")[0])
                    }
                    return nil
                }
        }

        XCTAssertEqual(
            Set(publicDeclarations),
            [
                "AuthConfiguration",
                "AuthFeatureFactory",
                "AuthFlowView",
                "AuthSessionModel",
                "SessionState"
            ]
        )
    }
}

private final class FactoryCheckSessionUseCase: CheckSessionUseCase, @unchecked Sendable {

    private let result: Bool

    init(result: Bool) {
        self.result = result
    }

    func execute() async throws -> Bool {
        result
    }
}

private final class FactorySessionSecretStore: SessionSecretStore, @unchecked Sendable {

    private var secret: String?

    init(initial: String?) {
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

private func XCTAssertChecking(
    _ state: SessionState,
    file: StaticString = #filePath,
    line: UInt = #line
) {
    guard case .checking = state else {
        return XCTFail("Expected checking state, got \(state)", file: file, line: line)
    }
}

private func XCTAssertFactoryActive(
    _ state: SessionState,
    file: StaticString = #filePath,
    line: UInt = #line
) {
    guard case .active = state else {
        return XCTFail("Expected active state, got \(state)", file: file, line: line)
    }
}

private func XCTAssertFactorySignedOut(
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

private extension URL {

    func recursiveSwiftFiles() throws -> [URL] {
        guard let enumerator = FileManager.default.enumerator(
            at: self,
            includingPropertiesForKeys: [.isRegularFileKey]
        ) else {
            return []
        }

        return try enumerator.compactMap { item in
            guard let url = item as? URL else { return nil }
            let values = try url.resourceValues(forKeys: [.isRegularFileKey])
            return values.isRegularFile == true && url.pathExtension == "swift" ? url : nil
        }
    }
}
