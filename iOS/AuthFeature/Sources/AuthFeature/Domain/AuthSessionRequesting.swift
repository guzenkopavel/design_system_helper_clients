import Foundation

/// Public contract for bounded requests that must run with the current auth session.
public
protocol AuthSessionRequesting: Sendable {

    func execute(_ request: AuthSessionRequest) async throws -> AuthSessionResponse
}

public
struct AuthSessionRequest: Sendable {

    public enum Method: String, Sendable {
        case get = "GET"
        case post = "POST"
    }

    public let method: Method
    public let path: String
    public let queryItems: [URLQueryItem]

    let removesSessionOnSuccess: Bool

    private init(
        method: Method,
        path: String,
        queryItems: [URLQueryItem] = [],
        removesSessionOnSuccess: Bool = false
    ) {
        self.method = method
        self.path = path
        self.queryItems = queryItems
        self.removesSessionOnSuccess = removesSessionOnSuccess
    }

    public static func profile() -> AuthSessionRequest {
        AuthSessionRequest(method: .get, path: "/api/profile")
    }

    public static func interviewHistory(page: Int? = nil, pageSize: Int? = nil) -> AuthSessionRequest {
        var queryItems: [URLQueryItem] = []
        if let page {
            queryItems.append(URLQueryItem(name: "page", value: String(page)))
        }
        if let pageSize {
            queryItems.append(URLQueryItem(name: "pageSize", value: String(pageSize)))
        }
        return AuthSessionRequest(
            method: .get,
            path: "/api/interviews/history",
            queryItems: queryItems
        )
    }

    public static func logout() -> AuthSessionRequest {
        AuthSessionRequest(
            method: .post,
            path: "/api/auth/logout",
            removesSessionOnSuccess: true
        )
    }
}

public
struct AuthSessionResponse: Sendable {

    public let statusCode: Int
    public let data: Data

    public init(statusCode: Int, data: Data) {
        self.statusCode = statusCode
        self.data = data
    }
}

public
enum AuthSessionRequestError: Error, Equatable, Sendable {
    case invalidSession
    case backendFailure
}
