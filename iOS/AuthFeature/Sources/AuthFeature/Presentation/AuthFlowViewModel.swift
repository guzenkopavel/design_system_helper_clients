//
//  AuthFlowViewModel.swift
//  AuthFeature
//
//  Created by Pavel Guzenko on 16.07.2025.
//  Copyright © 2025 Eltex. All rights reserved.
//

import Foundation

/// Модель представления флоу авторизации с изоляцией главного действующего лица,
/// наблюдаемостью и политикой единственной активной задачи.
actor AuthFlowViewModel: ObservableObject {

    var state: AuthFlowState = .init()

    private let checkEmail: CheckEmailUseCase
    private let logIn: LogInUseCase
    private let registerAccount: RegisterAccountUseCase
    private let timeProvider: TimeProvider
    private let completeAuthentication: @MainActor @Sendable () -> Void

    private var email: String = ""
    private var password: String = ""
    private var task: Task<Void, Error>?
    private var generation: Int = 0

    init(
        checkEmail: CheckEmailUseCase,
        logIn: LogInUseCase,
        registerAccount: RegisterAccountUseCase,
        timeProvider: TimeProvider,
        completeAuthentication: @escaping @MainActor @Sendable () -> Void = {}
    ) {
        self.checkEmail = checkEmail
        self.logIn = logIn
        self.registerAccount = registerAccount
        self.timeProvider = timeProvider
        self.completeAuthentication = completeAuthentication
    }

    /// Единственный метод обработки действий.
    func send(_ action: AuthFlowAction) {
        handle(action)
    }

    private func handle(_ action: AuthFlowAction) {
        switch action {
        case .emailChanged(let value):
            email = value
            state.feedback = .none

        case .submitEmail:
            cancelCurrentTask()
            guard validateEmail() else { return }
            generation += 1
            let gen = generation
            state.phase = .loading
            task = Task {
                do {
                    let exists = try await checkEmail.execute(email)
                    await self.updateIfNeeded(gen: gen) {
                        $0.step = .password(
                            confirmedEmail: email,
                            isLogin: exists
                        )
                        $0.phase = .idle
                        $0.feedback = .none
                    }
                } catch {
                    await self.updateIfNeeded(gen: gen) {
                        $0.phase = .idle
                        $0.feedback = Self.mapError(error)
                    }
                }
            }

        case .passwordChanged(let value):
            password = value
            state.feedback = .none

        case .submitPassword:
            cancelCurrentTask()
            guard case .password(let confirmedEmail, let isLogin) = state.step,
                  validatePassword() else { return }
            generation += 1
            let gen = generation
            state.phase = .loading
            task = Task {
                do {
                    _ = try await Self.performAuth(
                        isLogin: isLogin,
                        email: confirmedEmail,
                        password: password,
                        logIn: self.logIn,
                        register: self.registerAccount
                    )
                    await self.updateIfNeeded(gen: gen) {
                        $0.phase = .idle
                        $0.feedback = .none
                    }
                    await self.completeAuthenticationIfNeeded(gen: gen)
                } catch {
                    await self.updateIfNeeded(gen: gen) {
                        $0.phase = .idle
                        $0.feedback = Self.mapError(error)
                    }
                }
            }

        case .toggleShowPassword:
            state.showPassword.toggle()

        case .backToEmail:
            cancelCurrentTask()
            password = ""
            state.step = .email
            state.phase = .idle
            state.feedback = .none
            state.password = ""

        case .retry:
            cancelCurrentTask()
            if case .password = state.step {
                handle(.submitPassword)
            } else {
                handle(.submitEmail)
            }
        }
    }

    // MARK: - Validation

    @discardableResult
    private func validateEmail() -> Bool {
        if email.isBlank() {
            state.feedback = .inputWarning(message: "Введите адрес электронной почты")
            return false
        }
        guard Self.isValidEmail(email) else {
            state.feedback = .inputWarning(message: "Некорректный адрес электронной почты")
            return false
        }
        return true
    }

    @discardableResult
    private func validatePassword() -> Bool {
        if password.isBlank() {
            state.feedback = .inputWarning(message: "Введите пароль")
            return false
        }
        if password.count < 6 {
            state.feedback = .inputWarning(message: "Пароль должен содержать не менее 6 символов")
            return false
        }
        return true
    }

    private static func isValidEmail(_ value: String) -> Bool {
        let atIndex = value.firstIndex(of: "@")
        guard let atIndex, atIndex > value.startIndex else { return false }
        let afterAt = value[value.index(after: atIndex)...]
        return afterAt.contains(".")
    }

    // MARK: - Helpers

    private func cancelCurrentTask() {
        task?.cancel()
        task = nil
    }

    private func updateIfNeeded(gen: Int, _ block: (inout AuthFlowState) -> Void) {
        guard gen == generation else { return }
        block(&state)
    }

    private func completeAuthenticationIfNeeded(gen: Int) async {
        guard gen == generation else { return }
        await completeAuthentication()
    }

    private static func performAuth(
        isLogin: Bool,
        email: String,
        password: String,
        logIn: LogInUseCase,
        register: RegisterAccountUseCase
    ) async throws -> String {
        if isLogin {
            return try await logIn.execute(email: email, password: password)
        } else {
            return try await register.execute(email: email, password: password)
        }
    }

    private static func mapError(_ error: Error) -> AuthFlowState.Feedback {
        switch error as? AuthError {
        case .invalidInput:
            return .credentialsError
        case .backendFailure:
            return .credentialsError
        case .emailAlreadyRegistered:
            return .emailTaken
        case .serverValidation:
            return .serverError
        case .rateLimited(let retryAfter):
            return .rateLimited(retryAfter: retryAfter)
        case .offline:
            return .offline
        case .sessionInvalid:
            return .credentialsError
        default:
            return .serverError
        }
    }
}

// MARK: - String extension

private extension String {
    func isBlank() -> Bool {
        trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }
}
