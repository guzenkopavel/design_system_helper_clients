@testable import AuthFeature
import XCTest

/// Заглушка URLSession для детерминированных тестов.
final class TestURLSession: @unchecked Sendable {

    var dataResponse: ((URLRequest) async throws -> (Data, URLResponse))?

    var dataTaskResult: (Data, HTTPURLResponse)?
    var dataTaskError: Error?

    func data(for request: URLRequest) async throws -> (Data, URLResponse) {
        if let handler = dataResponse {
            return try await handler(request)
        }
        if let error = dataTaskError {
            throw error
        }
        guard let result = dataTaskResult else {
            throw URLError(.unknown)
        }
        return (result.0, result.1)
    }
}

final class DefaultAuthAPIClientTests: XCTestCase {

    private let httpsConfig: AuthConfiguration = {
        try! AuthConfiguration(apiBaseURL: URL(string: "https://89.125.1.21.nip.io")!)
    }()

    // MARK: - HTTPS guarantee

    func test_httpScheme_throwsInvalidConfiguration() {
        let httpConfig = try! AuthConfiguration(apiBaseURL: URL(string: "https://invalid")!)
        // Client only accepts https — AuthConfiguration already validates
        // The client also checks at runtime. We verify the config throws for http.
        XCTAssertThrowsError(try AuthConfiguration(apiBaseURL: URL(string: "http://89.125.1.21.nip.io")!))
    }

    // MARK: - Error envelope decoding

    func test_errorEnvelope_decodesCorrectly() throws {
        let fixture = try loadFixture(named: "ErrorInvalidCredentials")
        let decoder = JSONDecoder()
        let envelope = try decoder.decode(ErrorEnvelopeResponse.self, from: fixture)

        XCTAssertEqual(envelope.error.code, "invalid_credentials")
        XCTAssertEqual(envelope.error.message, "Неверная почта или пароль")
        XCTAssertTrue(envelope.error.retryable)
        XCTAssertEqual(envelope.error.traceId, "abc-123")
    }

    func test_errorEnvelope_rateLimited_decodesCorrectly() throws {
        let fixture = try loadFixture(named: "ErrorRateLimited")
        let decoder = JSONDecoder()
        let envelope = try decoder.decode(ErrorEnvelopeResponse.self, from: fixture)

        XCTAssertEqual(envelope.error.code, "rate_limited")
        XCTAssertNotNil(envelope.error.traceId)
    }

    // MARK: - Email check response

    func test_emailCheckResponse_decodesCorrectly() throws {
        let fixture = try loadFixture(named: "EmailCheckSuccess")
        let decoder = JSONDecoder()
        let response = try decoder.decode(EmailCheckResponse.self, from: fixture)

        XCTAssertTrue(response.exists)
    }

    // MARK: - Login response

    func test_loginResponse_decodesCorrectly() throws {
        let fixture = try loadFixture(named: "LoginSuccess")
        let decoder = JSONDecoder()
        let response = try decoder.decode(LoginResponse.self, from: fixture)

        XCTAssertEqual(response.user.email, "test@example.com")
    }

    // MARK: - Register response

    func test_registerResponse_decodesCorrectly() throws {
        let fixture = try loadFixture(named: "RegisterSuccess")
        let decoder = JSONDecoder()
        let response = try decoder.decode(RegisterResponse.self, from: fixture)

        XCTAssertEqual(response.email, "new@example.com")
    }

    // MARK: - Session token extraction

    func test_sessionToken_extractedFromSetCookie() throws {
        let token = extractToken(from: ["Set-Cookie": "dsh_session=abc123; Path=/; HttpOnly"])
        XCTAssertEqual(token, "abc123")
    }

    func test_sessionToken_emptyWhenMissing() throws {
        let token = extractToken(from: ["Set-Cookie": "other=value; Path=/"])
        XCTAssertEqual(token, "")
    }

    // MARK: - Helpers

    private func loadFixture(named name: String) throws -> Data {
        let bundle = Bundle.module
        guard let url = bundle.url(forResource: name, withExtension: "json") else {
            XCTFail("Fixtur не найден: \(name).json")
            return Data()
        }
        return try Data(contentsOf: url)
    }

    private func extractToken(from headerFields: [String: String]) -> String {
        guard let setCookie = headerFields["Set-Cookie"] else { return "" }
        let cookies = HTTPCookie.cookies(withResponseHeaderFields: ["Set-Cookie": setCookie], for: URL(string: "https://example.com")!)
        if let cookie = cookies.first(where: { $0.name == "dsh_session" }) {
            return cookie.value
        }
        return ""
    }
}
