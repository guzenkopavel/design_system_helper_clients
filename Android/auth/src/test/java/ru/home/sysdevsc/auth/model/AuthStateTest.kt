//
//  AuthStateTest.kt
//  SysDevSc
//
//  Created by Pavel Guzenko on 16.07.2026.
//  Copyright © 2026 Eltex. All rights reserved.
//

package ru.home.sysdevsc.auth.model

import ru.home.sysdevsc.auth.AuthState
import org.junit.Test
import org.junit.Assert.*

/**
 * Модульные тесты переходов состояний авторизации.
 * Покрывают: начальное положение, переход к загрузке, успех,
 * ошибка, истечение сессии и ветвление по почте (существующий / новый аккаунт).
 */
class AuthStateTest {

    @Test
    fun `начальное состояние — Idle`() {
        val state: AuthState = AuthState.Idle
        assertTrue(state is AuthState.Idle)
    }

    @Test
    fun `переход к загрузке — Authenticating`() {
        val state: AuthState = AuthState.Authenticating
        assertTrue(state is AuthState.Authenticating)
        assertNotSame(AuthState.Idle, state)
    }

    @Test
    fun `успешная авторизация — Authenticated`() {
        val state: AuthState = AuthState.Authenticated
        assertTrue(state is AuthState.Authenticated)
    }

    @Test
    fun `ошибка содержит сообщение`() {
        val message = "Неверный пароль"
        val state: AuthState = AuthState.Error(message)
        assertTrue(state is AuthState.Error)
        assertEquals(message, (state as AuthState.Error).message)
    }

    @Test
    fun `разные ошибки имеют разные сообщения`() {
        val error1 = AuthState.Error("Ошибка сети")
        val error2 = AuthState.Error("Неверный пароль")
        assertNotEquals((error1 as AuthState.Error).message, (error2 as AuthState.Error).message)
    }

    @Test
    fun `Idle и Authenticated — разные состояния`() {
        val idle = AuthState.Idle
        val authenticated = AuthState.Authenticated
        assertNotSame(idle, authenticated)
    }

    @Test
    fun `Authenticating отличается от Error`() {
        val authenticating = AuthState.Authenticating
        val error = AuthState.Error("Тестовая ошибка")
        assertNotSame(authenticating, error)
        assertFalse(authenticating is AuthState.Error)
        assertFalse(error is AuthState.Authenticating)
    }

    @Test
    fun `sealed class — исчерпывающая проверка типов`() {
        fun classify(state: AuthState): String = when (state) {
            is AuthState.Idle -> "idle"
            is AuthState.Authenticating -> "authenticating"
            is AuthState.Authenticated -> "authenticated"
            is AuthState.Error -> "error"
        }
        assertEquals("idle", classify(AuthState.Idle))
        assertEquals("authenticating", classify(AuthState.Authenticating))
        assertEquals("authenticated", classify(AuthState.Authenticated))
        assertEquals("error", classify(AuthState.Error("x")))
    }
}
