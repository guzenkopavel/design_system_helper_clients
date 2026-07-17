//
//  CheckEmailUseCaseTests.swift
//  AuthFeature
//
//  Created by Pavel Guzenko on 16.07.2025.
//  Copyright © 2025 Eltex. All rights reserved.
//

@testable import AuthFeature
import XCTest

final class FakeAuthAPIClientForCheckEmail: AuthAPIClient, @unchecked Sendable {

    var checkEmailResult: Result<Bool, Error>!
    var checkSessionCalled = false
    var loginCalled = false
    var registerCalled = false

    func checkEmail(_ email: String) async throws -> Bool {
        try checkEmailResult.get()
    }

    func login(email: String, password: String) async throws -> String {
        loginCalled = true
        fatalError("not configured")
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

final class CheckEmailUseCaseTests: XCTestCase {

    private var fakeClient: FakeAuthAPIClientForCheckEmail!
    private var useCase: CheckEmailUseCase!

    override func setUp() {
        super.setUp()
        fakeClient = FakeAuthAPIClientForCheckEmail()
        useCase = DefaultCheckEmailUseCase(client: fakeClient)
    }

    func test_execute_delegatesToClient() async throws {
        fakeClient.checkEmailResult = .success(true)
        let result = try await useCase.execute("test@example.com")
        XCTAssertTrue(result)
    }

    func test_execute_returnsFalse() async throws {
        fakeClient.checkEmailResult = .success(false)
        let result = try await useCase.execute("new@example.com")
        XCTAssertFalse(result)
    }

    func test_execute_propagatesError() async throws {
        fakeClient.checkEmailResult = .failure(AuthError.offline)
        do {
            _ = try await useCase.execute("test@example.com")
            XCTFail("должно бросить ошибку")
        } catch AuthError.offline {
            // Ожидается
        } catch {
            XCTFail("неожиданная ошибка: \(error)")
        }
    }
}
