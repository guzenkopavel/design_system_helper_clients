//
//  LogInUseCaseTests.swift
//  AuthFeature
//
//  Created by Pavel Guzenko on 16.07.2025.
//  Copyright © 2025 Eltex. All rights reserved.
//

@testable import AuthFeature
import XCTest

final class FakeAuthAPIClientForLogin: AuthAPIClient, @unchecked Sendable {

    var loginToken = ""
    var loginError: Error?
    var checkEmailCalled = false
    var checkSessionCalled = false
    var registerCalled = false

    func checkEmail(_ email: String) async throws -> Bool {
        checkEmailCalled = true
        fatalError("not configured")
    }

    func login(email: String, password: String) async throws -> String {
        if let error = loginError { throw error }
        return loginToken
    }

    func register(email: String, password: String) async throws -> String {
        registerCalled = true
        fatalError("not configured")
    }

    func checkSession(token: String) async throws -> Bool {
        checkSessionCalled = true
        fatalError("not configured")
    }
}

final class LogInUseCaseTests: XCTestCase {

    private var fakeClient: FakeAuthAPIClientForLogin!
    private var fakeStore: InMemorySessionSecretStore!
    private var useCase: LogInUseCase!

    override func setUp() {
        super.setUp()
        fakeClient = FakeAuthAPIClientForLogin()
        fakeStore = InMemorySessionSecretStore()
        useCase = DefaultLogInUseCase(client: fakeClient, store: fakeStore)
    }

    func test_execute_savesToken() async throws {
        fakeClient.loginToken = "token-123"
        let token = try await useCase.execute(email: "test@example.com", password: "password")
        XCTAssertEqual(token, "token-123")
        let stored = try await fakeStore.load()
        XCTAssertEqual(stored, "token-123")
    }

    func test_execute_propagatesError() async throws {
        fakeClient.loginError = AuthError.offline
        do {
            _ = try await useCase.execute(email: "test@example.com", password: "password")
            XCTFail("должно бросить ошибку")
        } catch AuthError.offline {
            // Ожидается
        } catch {
            XCTFail("неожиданная ошибка: \(error)")
        }
    }
}
