@testable import AuthFeature
import XCTest

final class AuthSessionRequestClientTests: XCTestCase {

    private let httpsConfig: AuthConfiguration = {
        try! AuthConfiguration(apiBaseURL: URL(string: "https://89.125.1.21.nip.io")!)
    }()

    private let cookieName = "dsh_" + "session"

    @MainActor
    func test_factoryBuildsPublicSessionContract() throws {
        let client = AuthFeatureFactory().makeSessionRequestClient(configuration: httpsConfig)

        withExtendedLifetime(client) {
            XCTAssertEqual(AuthSessionRequest.profile().path, "/api/profile")
        }
    }

    func test_sessionRequestClient_sendsCookieAndProfileRoute() async throws {
        let testSession = SessionRequestTestURLSession()
        let value = "fixture-value"
        let store = RecordingSessionSecretStoreForSessionRequest(secret: value)
        let sessionClient = DefaultAuthSessionRequestClient(
            configuration: httpsConfig,
            store: store,
            session: testSession
        )
        let responseBody = Data(#"{"ok":true}"#.utf8)

        testSession.dataResponse = { request in
            XCTAssertEqual(request.url?.absoluteString, "https://89.125.1.21.nip.io/api/profile")
            XCTAssertEqual(request.httpMethod, "GET")
            XCTAssertEqual(request.value(forHTTPHeaderField: "Cookie"), "\(self.cookieName)=\(value)")
            let response = HTTPURLResponse(
                url: request.url!,
                statusCode: 200,
                httpVersion: nil,
                headerFields: nil
            )!
            return (responseBody, response)
        }

        let response = try await sessionClient.execute(AuthSessionRequest.profile())

        XCTAssertEqual(response.statusCode, 200)
        XCTAssertEqual(response.data, responseBody)
        XCTAssertEqual(store.secret, value)
    }

    func test_sessionRequestClient_usesLogoutRouteAndClearsSecretAfterSuccess() async throws {
        let testSession = SessionRequestTestURLSession()
        let value = "logout-fixture"
        let store = RecordingSessionSecretStoreForSessionRequest(secret: value)
        let sessionClient = DefaultAuthSessionRequestClient(
            configuration: httpsConfig,
            store: store,
            session: testSession
        )

        testSession.dataResponse = { request in
            XCTAssertEqual(request.url?.absoluteString, "https://89.125.1.21.nip.io/api/auth/logout")
            XCTAssertEqual(request.httpMethod, "POST")
            XCTAssertEqual(request.value(forHTTPHeaderField: "Cookie"), "\(self.cookieName)=\(value)")
            let response = HTTPURLResponse(
                url: request.url!,
                statusCode: 204,
                httpVersion: nil,
                headerFields: nil
            )!
            return (Data(), response)
        }

        let response = try await sessionClient.execute(AuthSessionRequest.logout())

        XCTAssertEqual(response.statusCode, 204)
        XCTAssertNil(store.secret)
        XCTAssertEqual(store.removeCallCount, 1)
    }

    func test_sessionRequestClient_maps401AndClearsSecret() async throws {
        let testSession = SessionRequestTestURLSession()
        let value = "expired-fixture"
        let store = RecordingSessionSecretStoreForSessionRequest(secret: value)
        let sessionClient = DefaultAuthSessionRequestClient(
            configuration: httpsConfig,
            store: store,
            session: testSession
        )

        testSession.dataResponse = { request in
            let response = HTTPURLResponse(
                url: request.url!,
                statusCode: 401,
                httpVersion: nil,
                headerFields: nil
            )!
            return (Data(), response)
        }

        do {
            _ = try await sessionClient.execute(AuthSessionRequest.profile())
            XCTFail("Expected invalid session error")
        } catch AuthSessionRequestError.invalidSession {
            XCTAssertNil(store.secret)
            XCTAssertEqual(store.removeCallCount, 1)
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
    }

    func test_sessionRequestClient_keepsSecretWhenLogoutBackendFails() async throws {
        let testSession = SessionRequestTestURLSession()
        let value = "retryable-fixture"
        let store = RecordingSessionSecretStoreForSessionRequest(secret: value)
        let sessionClient = DefaultAuthSessionRequestClient(
            configuration: httpsConfig,
            store: store,
            session: testSession
        )

        testSession.dataResponse = { request in
            let response = HTTPURLResponse(
                url: request.url!,
                statusCode: 500,
                httpVersion: nil,
                headerFields: nil
            )!
            return (Data(), response)
        }

        do {
            _ = try await sessionClient.execute(AuthSessionRequest.logout())
            XCTFail("Expected backend failure")
        } catch AuthSessionRequestError.backendFailure {
            XCTAssertEqual(store.secret, value)
            XCTAssertEqual(store.removeCallCount, 0)
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
    }
}

final class SessionRequestTestURLSession: URLSessionDataLoading, @unchecked Sendable {

    var dataResponse: ((URLRequest) async throws -> (Data, URLResponse))?

    func data(for request: URLRequest) async throws -> (Data, URLResponse) {
        guard let dataResponse else {
            throw URLError(.unknown)
        }
        return try await dataResponse(request)
    }
}

final class RecordingSessionSecretStoreForSessionRequest: SessionSecretStore, @unchecked Sendable {

    var secret: String?
    private(set) var removeCallCount = 0

    init(secret: String? = nil) {
        self.secret = secret
    }

    func save(_ secret: String) async throws {
        self.secret = secret
    }

    func load() async throws -> String? {
        secret
    }

    func remove() async throws {
        removeCallCount += 1
        secret = nil
    }
}
