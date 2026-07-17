//
//  RegisterAccountUseCaseTests.swift
//  AuthFeature
//
//  Created by Pavel Guzenko on 16.07.2025.
//  Copyright © 2025 Eltex. All rights reserved.
//

@testable import AuthFeature
import XCTest

final class FakeAuthAPIClientForRegister: AuthAPIClient, @unchecked Sendable {

    var registerToken = ""
    var registerError: Error?
    var checkEmailCalled = false
    var checkSessionCalled = false
    var loginCalled = false

    func checkEmail(_ email: String) async throws -> Bool {
        checkEmailCalled = true
        fatalError("not configured")
    }

    func login(email: String, password: String) async throws -> String {
        loginCalled = true
        fatalError("not configured")
    }

    func register(email: String, password: String) async throws -> String {
        if let error = registerError { throw error }
        return registerToken
    }

    func checkSession(token: String) async throws -> Bool {
        checkSessionCalled = true
        fatalError("not configured")
    }
}

final class RegisterAccountUseCaseTests: XCTestCase {

    private var fakeClient: FakeAuthAPIClientForRegister!
    private var fakeStore: InMemorySessionSecretStore!
    private var useCase: RegisterAccountUseCase!

    override func setUp() {
        super.setUp()
        fakeClient = FakeAuthAPIClientForRegister()
        fakeStore = InMemorySessionSecretStore()
        useCase = DefaultRegisterAccountUseCase(client: fakeClient, store: fakeStore)
    }

    func test_execute_savesToken() async throws {
        fakeClient.registerToken = "reg-token-456"
        let token = try await useCase.execute(email: "new@example.com", password: "password")
        XCTAssertEqual(token, "reg-token-456")
        let stored = try await fakeStore.load()
        XCTAssertEqual(stored, "reg-token-456")
    }

    func test_execute_propagatesError() async throws {
        fakeClient.registerError = AuthError.offline
        do {
            _ = try await useCase.execute(email: "new@example.com", password: "password")
            XCTFail("должно бросить ошибку")
        } catch AuthError.offline {
            // Ожидается
        } catch {
            XCTFail("неожиданная ошибка: \(error)")
        }
    }
}
