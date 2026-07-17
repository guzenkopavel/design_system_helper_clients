//
//  AuthFlowState.swift
//  AuthFeature
//
//  Created by Pavel Guzenko on 16.07.2025.
//  Copyright © 2025 Eltex. All rights reserved.
//

import Foundation

/// Семантическое значение состояния флоу авторизации.
struct AuthFlowState: Equatable, Sendable {

    /// Текущий шаг флоу.
    enum Step: Equatable, Sendable {
        case email
        case password(confirmedEmail: String, isLogin: Bool)
    }

    /// Фаза взаимодействия.
    enum Phase: Equatable, Sendable {
        case idle
        case loading
    }

    /// Обратная связь с пользователем.
    enum Feedback: Equatable, Sendable {
        case none
        case inputWarning(message: String)
        case credentialsError
        case emailTaken
        case serverError
        case rateLimited(retryAfter: Date)
        case offline
    }

    var step: Step
    var phase: Phase
    var feedback: Feedback
    var password: String
    var showPassword: Bool

    init(
        step: Step = .email,
        phase: Phase = .idle,
        feedback: Feedback = .none,
        password: String = "",
        showPassword: Bool = false
    ) {
        self.step = step
        self.phase = phase
        self.feedback = feedback
        self.password = password
        self.showPassword = showPassword
    }
}
