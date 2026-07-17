//
//  AuthFlowAction.swift
//
//  Created by Pavel Guzenko on 16.07.2025.
//  Copyright © 2025 Eltex. All rights reserved.
//

/// Типизированные действия пользователя.
enum AuthFlowAction: Sendable {

    case emailChanged(String)
    case submitEmail
    case passwordChanged(String)
    case submitPassword
    case toggleShowPassword
    case backToEmail
    case retry
}
