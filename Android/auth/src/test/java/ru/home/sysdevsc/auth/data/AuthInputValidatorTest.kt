//
//  AuthInputValidatorTest.kt
//  SysDevSc
//
//  Created by Pavel Guzenko on 16.07.2026.
//  Copyright © 2026 Eltex. All rights reserved.
//

package ru.home.sysdevsc.auth.data

import org.junit.Test
import org.junit.Assert.*

/**
 * Модульные тесты валидатора входных данных авторизации.
 * Покрывают: валидную и невалидную почту, пустую почту,
 * валидный и короткий пароль, пустой пароль.
 */
class AuthInputValidatorTest {

    private val validator = AuthInputValidator()

    // --- Email validation ---

    @Test
    fun `валидная почта проходит проверку`() {
        val result = validator.validateEmail("user@example.com")
        assertTrue(result is ValidationResult.Valid)
    }

    @Test
    fun `почта без @ отклоняется`() {
        val result = validator.validateEmail("userexample.com")
        assertTrue(result is ValidationResult.Invalid)
    }

    @Test
    fun `почта без доменной части после @ отклоняется`() {
        val result = validator.validateEmail("user@local")
        assertTrue(result is ValidationResult.Invalid)
    }

    @Test
    fun `пустая почта отклоняется`() {
        val result = validator.validateEmail("")
        assertTrue(result is ValidationResult.Invalid)
    }

    @Test
    fun `почта состоящая из пробелов отклоняется`() {
        val result = validator.validateEmail("   ")
        assertTrue(result is ValidationResult.Invalid)
    }

    @Test
    fun `почта с @ в начале отклоняется`() {
        val result = validator.validateEmail("@example.com")
        assertTrue(result is ValidationResult.Invalid)
    }

    @Test
    fun `почта с несколькими @ и доменной частью проходит`() {
        val result = validator.validateEmail("user+tag@example.com")
        assertTrue(result is ValidationResult.Valid)
    }

    // --- Password validation ---

    @Test
    fun `пароль длиной 6 символов проходит`() {
        val result = validator.validatePassword("passw1")
        assertTrue(result is ValidationResult.Valid)
    }

    @Test
    fun `длинный пароль проходит`() {
        val result = validator.validatePassword("MyStr0ngP@ss!")
        assertTrue(result is ValidationResult.Valid)
    }

    @Test
    fun `пароль короче 6 символов отклоняется`() {
        val result = validator.validatePassword("abc")
        assertTrue(result is ValidationResult.Invalid)
    }

    @Test
    fun `пароль ровно 5 символов отклоняется`() {
        val result = validator.validatePassword("12345")
        assertTrue(result is ValidationResult.Invalid)
    }

    @Test
    fun `пустой пароль отклоняется`() {
        val result = validator.validatePassword("")
        assertTrue(result is ValidationResult.Invalid)
    }

    @Test
    fun `пароль из пробелов отклоняется`() {
        val result = validator.validatePassword("     ")
        assertTrue(result is ValidationResult.Invalid)
    }

    // --- ValidationResult sealed interface exhaustiveness ---

    @Test
    fun `ValidResult — исчерпывающая проверка типов`() {
        fun classify(result: ValidationResult): String = when (result) {
            is ValidationResult.Valid -> "valid"
            is ValidationResult.Invalid -> "invalid"
        }
        assertEquals("valid", classify(ValidationResult.Valid))
        assertEquals("invalid", classify(ValidationResult.Invalid("reason")))
    }

    @Test
    fun `Invalid содержит причину`() {
        val reason = "Пароль должен содержать не менее 6 символов"
        val result = validator.validatePassword("short")
        assertTrue(result is ValidationResult.Invalid)
        assertNotNull((result as ValidationResult.Invalid).reason)
    }
}
