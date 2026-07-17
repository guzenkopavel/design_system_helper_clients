//
//  CheckSessionUseCaseTests.swift
//  AuthFeature
//
//  Created by Pavel Guzenko on 16.07.2025.
//  Copyright © 2025 Eltex. All rights reserved.
//

@testable import AuthFeature
import XCTest

final class FakeAuthAPIClientForSession: AuthAPIClient, @unchecked Sendable {

    var sessionValid = true
    var sessionError: Error?
    var checkEmailCalled = false
    var loginCalled = false
    var registerCalled = false

    func checkEmail(_ email: String) async throws -> Bool {
        checkEmailCalled = true
        fatalError("not configured")
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
        if let error = sessionError { throw error }
        return sessionValid
    }
}

final class CheckSessionUseCaseTests: XCTestCase {

    private var fakeClient: FakeAuthAPIClientForSession!
    private var fakeStore: InMemorySessionSecretStore!
    private var useCase: CheckSessionUseCase!

    override func setUp() {
        super.setUp()
        fakeClient = FakeAuthAPIClientForSession()
        fakeStore = InMemorySessionSecretStore()
        useCase = DefaultCheckSessionUseCase(client: fakeClient, store: fakeStore)
    }

    func test_execute_noToken_returnsFalse() async throws {
        let result = try await useCase.execute()
        XCTAssertFalse(result)
    }

    func test_execute_validSession_returnsTrue() async throws {
        try await fakeStore.save("valid-token")
        fakeClient.sessionValid = true
        let result = try await useCase.execute()
        XCTAssertTrue(result)
    }

    func test_execute_invalidSession_clearsStore() async throws {
        try await fakeStore.save("old-token")
        fakeClient.sessionError = AuthError.sessionInvalid
        do {
            let result = try await useCase.execute()
            XCTAssertFalse(result)
        } catch {
            XCTFail("не должно бросать ошибку при недействительной сессии")
        }
        let stored = try await fakeStore.load()
        XCTAssertNil(stored)
    }

    func test_execute_propagatesOtherErrors() async throws {
        try await fakeStore.save("token")
        fakeClient.sessionError = AuthError.offline
        do {
            _ = try await useCase.execute()
            XCTFail("должно бросить ошибку")
        } catch AuthError.offline {
            // Ожидается
        } catch {
            XCTFail("неожиданная ошибка: \(error)")
        }
    }
}
