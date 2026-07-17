//
//  DefaultAuthAPIClient.swift
//  AuthFeature
//
//  Created by Pavel Guzenko on 16.07.2025.
//  Copyright © 2025 Eltex. All rights reserved.
//

import Foundation

/// Реализация AuthAPIClient поверх URLSession с ephemeral конфигурацией.
internal actor DefaultAuthAPIClient: AuthAPIClient {

    private let configuration: AuthConfiguration
    private let session: URLSession

    /// Инициализация с конфигурацией и опциональным секретом сессии.
    init(configuration: AuthConfiguration, sessionSecret: String? = nil) {
        self.configuration = configuration

        let sessionConfig = URLSessionConfiguration.ephemeral
        sessionConfig.httpShouldSetCookies = false
        sessionConfig.httpCookieAcceptPolicy = .never
        sessionConfig.urlCache = nil

        self.session = URLSession(configuration: sessionConfig)
    }

    // MARK: - AuthAPIClient

    nonisolated func checkEmail(_ email: String) async throws -> Bool {
        let client = self
        let response: EmailCheckResponse = try await client.performRequest(
            path: "/api/auth/email-check",
            method: "POST",
            body: ["email": email],
            token: nil,
            responseType: EmailCheckResponse.self
        )
        return response.exists
    }

    nonisolated func login(email: String, password: String) async throws -> String {
        let client = self
        return try await client.performLoginOrRegister(
            path: "/api/auth/login",
            body: ["email": email, "password": password]
        )
    }

    nonisolated func register(email: String, password: String) async throws -> String {
        let client = self
        return try await client.performLoginOrRegister(
            path: "/api/auth/register",
            body: ["email": email, "password": password]
        )
    }

    nonisolated func checkSession(token: String) async throws -> Bool {
        let client = self
        let _: ProfileResponse = try await client.performRequest(
            path: "/api/profile",
            method: "GET",
            body: nil,
            token: token,
            responseType: ProfileResponse.self
        )
        return true
    }

    // MARK: - Internal

    private func buildURL(path: String) -> URL {
        var components = URLComponents(url: configuration.apiBaseURL, resolvingAgainstBaseURL: false)!
        components.path += path
        return components.url!
    }

    private func performRequest<T: Decodable>(
        path: String,
        method: String,
        body: [String: String]?,
        token: String?,
        responseType: T.Type
    ) async throws -> T {
        var request = URLRequest(url: buildURL(path: path))
        request.httpMethod = method

        if let body {
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }

        if let token {
            request.setValue("Cookie: dsh_session=\(token)", forHTTPHeaderField: "Cookie")
        }

        guard configuration.apiBaseURL.scheme == "https" else {
            throw AuthError.invalidConfiguration
        }

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw AuthError.backendFailure(traceID: nil)
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            throw handleErrorResponse(
                data: data,
                statusCode: httpResponse.statusCode,
                headers: httpResponse.allHeaderFields as! [String: String]
            )
        }

        do {
            let decoder = JSONDecoder()
            return try decoder.decode(T.self, from: data)
        } catch {
            throw AuthError.backendFailure(traceID: nil)
        }
    }

    private func performLoginOrRegister(path: String, body: [String: String]) async throws -> String {
        var request = URLRequest(url: buildURL(path: path))
        request.httpMethod = "POST"
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        guard configuration.apiBaseURL.scheme == "https" else {
            throw AuthError.invalidConfiguration
        }

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw AuthError.backendFailure(traceID: nil)
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            throw handleErrorResponse(
                data: data,
                statusCode: httpResponse.statusCode,
                headers: httpResponse.allHeaderFields as! [String: String]
            )
        }

        return extractSessionToken(from: httpResponse.allHeaderFields as! [String: String])
    }

    private func extractSessionToken(from headerFields: [String: String]) -> String {
        guard let setCookie = headerFields["Set-Cookie"] else { return "" }
        let cookies = HTTPCookie.cookies(
            withResponseHeaderFields: ["Set-Cookie": setCookie],
            for: configuration.apiBaseURL
        )
        if let cookie = cookies.first(where: { $0.name == "dsh_session" }) {
            return cookie.value
        }
        return ""
    }

    private func handleErrorResponse(data: Data, statusCode: Int, headers: [String: String]) -> AuthError {
        let retryAfter = parseRetryAfter(from: headers)

        switch statusCode {
        case 401:
            return .sessionInvalid
        case 409:
            return .emailAlreadyRegistered
        case 422:
            do {
                let decoder = JSONDecoder()
                let envelope = try decoder.decode(ErrorEnvelopeResponse.self, from: data)
                return .serverValidation(message: envelope.error.message)
            } catch {
                return .serverValidation(message: "Ошибка валидации сервера")
            }
        case 429:
            if let retryAfter {
                return .rateLimited(retryAfter: retryAfter)
            }
            return .serverValidation(message: "Слишком много попыток")
        default:
            do {
                let decoder = JSONDecoder()
                let envelope = try decoder.decode(ErrorEnvelopeResponse.self, from: data)
                return .backendFailure(traceID: envelope.error.traceId)
            } catch {
                return .backendFailure(traceID: nil)
            }
        }
    }

    private func parseRetryAfter(from headers: [String: String]) -> Date? {
        guard let value = headers["Retry-After"] ?? headers["retry-after"] else {
            return nil
        }

        if let seconds = Int(value) {
            return Date(timeIntervalSinceNow: Double(seconds))
        }

        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en-US_POSIX")
        formatter.dateFormat = "EEE, dd MMM yyyy HH:mm:ss 'GMT'"
        return formatter.date(from: value)
    }
}
