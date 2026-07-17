import AuthFeature
import Foundation

internal struct MyProfilePreviewSessionClient: AuthSessionRequesting {
    private static let profileRequest = AuthSessionRequest.profile()
    private static let historyRequest = AuthSessionRequest.interviewHistory()
    private static let logoutRequest = AuthSessionRequest.logout()

    private let scenario: Scenario

    internal init(arguments: [String]) {
        scenario = Scenario(arguments: arguments)
    }

    internal func execute(_ request: AuthSessionRequest) async throws -> AuthSessionResponse {
        switch scenario {
        case .invalidSession:
            throw AuthSessionRequestError.invalidSession
        case _ where request.method == Self.profileRequest.method && request.path == Self.profileRequest.path:
            return AuthSessionResponse(statusCode: 200, data: Data(#"{"email":"pavel@example.com"}"#.utf8))
        case .empty where request.method == Self.historyRequest.method && request.path == Self.historyRequest.path:
            return AuthSessionResponse(statusCode: 200, data: Data(#"{"data":[],"page":{"hasMore":false}}"#.utf8))
        case .historyError where request.method == Self.historyRequest.method && request.path == Self.historyRequest.path:
            throw URLError(.notConnectedToInternet)
        case _ where request.method == Self.historyRequest.method && request.path == Self.historyRequest.path:
            return AuthSessionResponse(statusCode: 200, data: Data(#"{"data":[{},{},{}],"page":{"hasMore":false}}"#.utf8))
        case .logoutFailure where request.method == Self.logoutRequest.method && request.path == Self.logoutRequest.path:
            throw AuthSessionRequestError.backendFailure
        case _ where request.method == Self.logoutRequest.method && request.path == Self.logoutRequest.path:
            return AuthSessionResponse(statusCode: 204, data: Data())
        default:
            throw AuthSessionRequestError.backendFailure
        }
    }

    private enum Scenario {
        case content
        case empty
        case historyError
        case invalidSession
        case logoutFailure

        init(arguments: [String]) {
            if arguments.contains("--profile-stub-empty") || arguments.contains("--auth-stub-signed-out") {
                self = .empty
            } else if arguments.contains("--profile-stub-history-error") {
                self = .historyError
            } else if arguments.contains("--profile-stub-invalid-session") || arguments.contains("--auth-stub-invalid-session") {
                self = .invalidSession
            } else if arguments.contains("--profile-stub-logout-failure") {
                self = .logoutFailure
            } else {
                self = .content
            }
        }
    }
}

extension MyProfileFeatureFactory {
    public func makePreviewSessionClient(arguments: [String]) -> any AuthSessionRequesting {
        MyProfilePreviewSessionClient(arguments: arguments)
    }
}
