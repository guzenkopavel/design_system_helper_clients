@testable import MyProfileFeature
import AuthFeature
import Foundation
import XCTest

final class MyProfileAPIClientTests: XCTestCase {

    func test_fetchProfile_buildsProfileRequestAndDecodesEmail() async throws {
        let session = RecordingSessionClient(responses: [
            .success(json(#"{"email":"pavel@example.com"}"#))
        ])
        let client = MyProfileAPIClient(sessionClient: session)

        let profile = try await client.fetchProfile()
        let requests = await session.requests

        XCTAssertEqual(profile.email, "pavel@example.com")
        XCTAssertEqual(requests.map(\.path), ["/api/profile"])
        XCTAssertEqual(requests.first?.method, .get)
    }

    func test_fetchInterviewCount_loadsAllPagesUntilHasMoreIsFalse() async throws {
        let session = RecordingSessionClient(responses: [
            .success(json(#"{"data":[{},{}],"page":{"hasMore":true,"nextCursor":"two"}}"#)),
            .success(json(#"{"data":[{}],"page":{"hasMore":false}}"#))
        ])
        let client = MyProfileAPIClient(sessionClient: session)

        let count = try await client.fetchInterviewCount()
        let requests = await session.requests

        XCTAssertEqual(count, 3)
        XCTAssertEqual(requests.map(\.path), ["/api/interviews/history", "/api/interviews/history"])
        XCTAssertEqual(requests[0].queryItems, [
            URLQueryItem(name: "page", value: "1"),
            URLQueryItem(name: "pageSize", value: "20")
        ])
        XCTAssertEqual(requests[1].queryItems, [
            URLQueryItem(name: "page", value: "2"),
            URLQueryItem(name: "pageSize", value: "20")
        ])
    }

    func test_fetchProfile_maps401ToInvalidSession() async {
        let session = RecordingSessionClient(responses: [
            .failure(AuthSessionRequestError.invalidSession)
        ])
        let client = MyProfileAPIClient(sessionClient: session)

        do {
            _ = try await client.fetchProfile()
            XCTFail("Expected invalid session")
        } catch let error as MyProfileFeatureError {
            XCTAssertEqual(error, .invalidSession)
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
    }

    func test_fetchInterviewCount_mapsOfflineError() async {
        let session = RecordingSessionClient(responses: [
            .failure(URLError(.notConnectedToInternet))
        ])
        let client = MyProfileAPIClient(sessionClient: session)

        do {
            _ = try await client.fetchInterviewCount()
            XCTFail("Expected offline error")
        } catch let error as MyProfileFeatureError {
            XCTAssertEqual(error, .offline)
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
    }

    func test_logout_usesLogoutRouteAndMapsBackendFailure() async {
        let session = RecordingSessionClient(responses: [
            .failure(AuthSessionRequestError.backendFailure)
        ])
        let client = MyProfileAPIClient(sessionClient: session)

        do {
            try await client.logout()
            XCTFail("Expected backend error")
        } catch let error as MyProfileFeatureError {
            XCTAssertEqual(error, .backend)
        } catch {
            XCTFail("Unexpected error: \(error)")
        }

        let requests = await session.requests
        XCTAssertEqual(requests.map(\.path), ["/api/auth/logout"])
        XCTAssertEqual(requests.first?.method, .post)
    }
}

private actor RecordingSessionClient: AuthSessionRequesting {

    private(set) var requests: [AuthSessionRequest] = []
    private var responses: [Result<AuthSessionResponse, Error>]

    init(responses: [Result<AuthSessionResponse, Error>]) {
        self.responses = responses
    }

    func execute(_ request: AuthSessionRequest) async throws -> AuthSessionResponse {
        requests.append(request)
        guard !responses.isEmpty else {
            throw AuthSessionRequestError.backendFailure
        }
        let next = responses.removeFirst()
        switch next {
        case let .success(response):
            return response
        case let .failure(error):
            throw error
        }
    }
}

private func json(_ raw: String) -> AuthSessionResponse {
    AuthSessionResponse(statusCode: 200, data: Data(raw.utf8))
}
