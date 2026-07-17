import Foundation

internal struct DefaultAuthSessionRequestClient: AuthSessionRequesting {

    private let configuration: AuthConfiguration
    private let store: SessionSecretStore
    private let session: URLSessionDataLoading

    internal init(
        configuration: AuthConfiguration,
        store: SessionSecretStore,
        session: URLSessionDataLoading? = nil
    ) {
        self.configuration = configuration
        self.store = store
        self.session = session ?? URLSession(configuration: Self.sessionConfiguration())
    }

    internal func execute(_ request: AuthSessionRequest) async throws -> AuthSessionResponse {
        guard let token = try await store.load() else {
            throw AuthSessionRequestError.invalidSession
        }

        do {
            let response = try await perform(request, token: token)
            if request.removesSessionOnSuccess {
                try await store.remove()
            }
            return response
        } catch AuthSessionRequestError.invalidSession {
            try await store.remove()
            throw AuthSessionRequestError.invalidSession
        }
    }

    private func perform(_ request: AuthSessionRequest, token: String) async throws -> AuthSessionResponse {
        guard configuration.apiBaseURL.scheme == "https" else {
            throw AuthSessionRequestError.backendFailure
        }

        var urlRequest = URLRequest(url: buildURL(path: request.path, queryItems: request.queryItems))
        urlRequest.httpMethod = request.method.rawValue
        urlRequest.setValue("dsh_session=\(token)", forHTTPHeaderField: "Cookie")

        let (data, response) = try await session.data(for: urlRequest)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw AuthSessionRequestError.backendFailure
        }
        guard (200...299).contains(httpResponse.statusCode) else {
            if httpResponse.statusCode == 401 {
                throw AuthSessionRequestError.invalidSession
            }
            throw AuthSessionRequestError.backendFailure
        }
        return AuthSessionResponse(statusCode: httpResponse.statusCode, data: data)
    }

    private func buildURL(path: String, queryItems: [URLQueryItem]) -> URL {
        var components = URLComponents(url: configuration.apiBaseURL, resolvingAgainstBaseURL: false)!
        components.path += path
        if !queryItems.isEmpty {
            components.queryItems = queryItems
        }
        return components.url!
    }

    private static func sessionConfiguration() -> URLSessionConfiguration {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.httpShouldSetCookies = false
        configuration.httpCookieAcceptPolicy = .never
        configuration.urlCache = nil
        return configuration
    }
}

extension AuthFeatureFactory {

    public func makeSessionRequestClient(configuration: AuthConfiguration) -> any AuthSessionRequesting {
        DefaultAuthSessionRequestClient(
            configuration: configuration,
            store: KeychainSessionSecretStore()
        )
    }
}

protocol URLSessionDataLoading: Sendable {

    func data(for request: URLRequest) async throws -> (Data, URLResponse)
}

extension URLSession: URLSessionDataLoading {}
