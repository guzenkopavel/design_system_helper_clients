//
//  AuthInputValidator.kt
//  SysDevSc
//
//  Created by Pavel Guzenko on 16.07.2026.
//  Copyright © 2026 Eltex. All rights reserved.
//

package ru.home.sysdevsc.auth.data

/**
 * Результат локальной валидации входных данных.
 */
sealed interface ValidationResult {
    data object Valid : ValidationResult
    data class Invalid(val reason: String) : ValidationResult
}

/**
 * Локальная валидация адреса почты и пароля до сетевого запроса.
 * Не зависит от Android Context или ресурсов — полностью доменный класс.
 *
 * Правила валидации почты:
 * - не пустой
 * - содержит символ '@'
 * - после '@' есть символ '.' (доменная часть)
 *
 * Правила валидации пароля:
 * - не пустой
 * - минимум 6 символов (требование регистрации)
 */
class AuthInputValidator {

    fun validateEmail(email: String): ValidationResult {
        if (email.isBlank()) {
            return ValidationResult.Invalid("Адрес электронной почты не может быть пустым")
        }
        val atIndex = email.indexOf('@')
        if (atIndex <= 0) {
            return ValidationResult.Invalid("Адрес должен содержать символ '@'")
        }
        val afterAt = email.substring(atIndex + 1)
        if (afterAt.isEmpty() || !afterAt.contains('.')) {
            return ValidationResult.Invalid("Адрес должен содержать доменную часть")
        }
        return ValidationResult.Valid
    }

    fun validatePassword(password: String): ValidationResult {
        if (password.isBlank()) {
            return ValidationResult.Invalid("Пароль не может быть пустым")
        }
        if (password.length < 6) {
            return ValidationResult.Invalid("Пароль должен содержать не менее 6 символов")
        }
        return ValidationResult.Valid
    }
}
