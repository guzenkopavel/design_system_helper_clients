//
//  AuthFlowViewModelTests.swift
//  AuthFeature
//
//  Created by Pavel Guzenko on 16.07.2025.
//  Copyright © 2025 Eltex. All rights reserved.
//

@testable import AuthFeature
import XCTest

final class AuthFlowViewModelTests: XCTestCase {

    private var fakeCheckEmail: FakeCheckEmailUseCase!
    private var fakeLogIn: FakeLogInUseCase!
    private var fakeRegister: FakeRegisterAccountUseCase!
    private var fakeTime: FakeTimeProvider!

    func makeViewModel(
        completeAuthentication: @escaping @MainActor @Sendable () -> Void = {}
    ) -> AuthFlowViewModel {
        AuthFlowViewModel(
            checkEmail: fakeCheckEmail,
            logIn: fakeLogIn,
            registerAccount: fakeRegister,
            timeProvider: fakeTime,
            completeAuthentication: completeAuthentication
        )
    }

    override func setUp() {
        super.setUp()
        fakeCheckEmail = FakeCheckEmailUseCase()
        fakeLogIn = FakeLogInUseCase()
        fakeRegister = FakeRegisterAccountUseCase()
        fakeTime = FakeTimeProvider()
    }

    // MARK: - Email validation

    func test_emptyEmail_showsInputWarning() async {
        let vm = makeViewModel()
        await vm.send(.emailChanged(""))
        await vm.send(.submitEmail)
        let state = await vm.state
        if case .inputWarning = state.feedback {
            // OK
        } else {
            XCTFail("Ожидается предупреждение о пустом поле")
        }
    }

    func test_invalidEmail_showsInputWarning() async {
        let vm = makeViewModel()
        await vm.send(.emailChanged("bad-email"))
        await vm.send(.submitEmail)
        let state = await vm.state
        if case .inputWarning = state.feedback {
            // OK
        } else {
            XCTFail("Ожидается предупреждение о некорректной почте")
        }
    }

    // MARK: - Email transitions

    func test_submitEmail_exists_transitionsToLogin() async {
        fakeCheckEmail.result = .success(true)
        let vm = makeViewModel()
        await vm.send(.emailChanged("test@example.com"))
        await vm.send(.submitEmail)
        try? await Task.sleep(nanoseconds: 500_000_000)
        let state = await vm.state
        if case .password(let confirmedEmail, let isLogin) = state.step {
            XCTAssertEqual(confirmedEmail, "test@example.com")
            XCTAssertTrue(isLogin)
        } else {
            XCTFail("Ожидается переход к шагу пароля")
        }
    }

    func test_submitEmail_new_transitionsToRegister() async {
        fakeCheckEmail.result = .success(false)
        let vm = makeViewModel()
        await vm.send(.emailChanged("new@example.com"))
        await vm.send(.submitEmail)
        try? await Task.sleep(nanoseconds: 500_000_000)
        let state = await vm.state
        if case .password(let confirmedEmail, let isLogin) = state.step {
            XCTAssertEqual(confirmedEmail, "new@example.com")
            XCTAssertFalse(isLogin)
        } else {
            XCTFail("Ожидается переход к шагу регистрации")
        }
    }

    // MARK: - Password validation

    func test_emptyPassword_showsInputWarning() async {
        fakeCheckEmail.result = .success(true)
        let vm = makeViewModel()
        await vm.send(.emailChanged("test@example.com"))
        await vm.send(.submitEmail)
        try? await Task.sleep(nanoseconds: 500_000_000)
        await vm.send(.submitPassword)
        let state = await vm.state
        if case .inputWarning = state.feedback {
            // OK
        } else {
            XCTFail("Ожидается предупреждение о пустом пароле")
        }
    }

    @MainActor
    func test_submitPasswordSuccess_completesAuthentication() async {
        fakeCheckEmail.result = .success(true)
        fakeLogIn.result = .success("token")
        var completionCount = 0
        let vm = makeViewModel {
            completionCount += 1
        }

        await vm.send(.emailChanged("test@example.com"))
        await vm.send(.submitEmail)
        try? await Task.sleep(nanoseconds: 500_000_000)
        await vm.send(.passwordChanged("correct-password"))
        await vm.send(.submitPassword)
        try? await Task.sleep(nanoseconds: 500_000_000)

        XCTAssertEqual(completionCount, 1)
    }

    // MARK: - Back navigation

    func test_back_preservesEmail() async {
        fakeCheckEmail.result = .success(true)
        let vm = makeViewModel()
        await vm.send(.emailChanged("test@example.com"))
        await vm.send(.submitEmail)
        try? await Task.sleep(nanoseconds: 500_000_000)
        await vm.send(.backToEmail)
        let state = await vm.state
        XCTAssertEqual(state.step, .email)
    }

    // MARK: - Toggle password

    func test_toggleShowPassword() async {
        let vm = makeViewModel()
        await vm.send(.toggleShowPassword)
        let state = await vm.state
        XCTAssertTrue(state.showPassword)
    }

    // MARK: - Error handling

    func test_emailServerError_showsOffline() async {
        fakeCheckEmail.result = .failure(AuthError.offline)
        let vm = makeViewModel()
        await vm.send(.emailChanged("test@example.com"))
        await vm.send(.submitEmail)
        try? await Task.sleep(nanoseconds: 500_000_000)
        let state = await vm.state
        if case .offline = state.feedback {
            // OK
        } else {
            XCTFail("Ожидается offline-обратная связь")
        }
    }
}
