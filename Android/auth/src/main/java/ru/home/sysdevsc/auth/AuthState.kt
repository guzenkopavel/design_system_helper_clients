//
//  AuthState.kt
//  SysDevSc
//
//  Created by Pavel Guzenko on 16.07.2026.
//  Copyright © 2026 Eltex. All rights reserved.
//

package ru.home.sysdevsc.auth

/**
 * Состояние авторизации.
 */
sealed class AuthState {

    /** Начальное состояние, проверка ещё не инициирована. */
    data object Idle : AuthState()

    /** Идёт проверка учётных данных. */
    data object Authenticating : AuthState()

    /** Успешная аутентификация. */
    data object Authenticated : AuthState()

    /** Ошибка авторизации. */
    data class Error(val message: String) : AuthState()
}
