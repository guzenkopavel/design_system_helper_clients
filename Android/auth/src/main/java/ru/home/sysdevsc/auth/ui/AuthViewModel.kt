//
//  AuthViewModel.kt
//  SysDevSc
//
//  Created by Pavel Guzenko on 16.07.2026.
//  Copyright © 2026 Eltex. All rights reserved.
//

package ru.home.sysdevsc.auth.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import ru.home.sysdevsc.auth.data.AuthApiService
import ru.home.sysdevsc.auth.data.AuthInputValidator
import ru.home.sysdevsc.auth.data.SessionRepository
import ru.home.sysdevsc.auth.data.ValidationResult
import ru.home.sysdevsc.auth.model.AuthResult

/**
 * Шаг двухшагового флоу авторизации.
 */
enum class AuthStep {
    Email,
    Password
}

/**
 * Тип локальной ошибки валидации. Используется UI-слоем для выбора
 * правильного строкового ресурса.
 */
sealed class ValidationError {
    data object EmptyEmail : ValidationError()
    data object EmptyPassword : ValidationError()
    data object InvalidEmail : ValidationError()
    data object ShortPassword : ValidationError()
}

/**
 * Тип серверной ошибки авторизации.
 */
sealed class ServerError {
    data object InvalidCredentials : ServerError()
    data object EmailTaken : ServerError()
    data object RateLimited : ServerError()
    data object Offline : ServerError()
    data class Custom(val message: String) : ServerError()
}

/**
 * Представление UI-состояния экранов авторизации.
 * Однонаправленный поток: UiState → Composable.
 */
data class UiState(
    val currentStep: AuthStep = AuthStep.Email,
    val email: String = "",
    val isLogin: Boolean = true,
    val isLoading: Boolean = false,
    val validationError: ValidationError? = null,
    val serverError: ServerError? = null,
    val isRateLimited: Boolean = false
)

/**
 * ViewModel для управления состоянием и логикой двухшагового
 * флоу авторизации. Не зависит от Android Context.
 */
class AuthViewModel(
    private val authApiService: AuthApiService,
    private val sessionRepository: SessionRepository
) : ViewModel() {

    private val validator = AuthInputValidator()

    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    /**
     * Обновляет адрес электронной почты и очищает ошибки.
     */
    fun onEmailChanged(email: String) {
        _uiState.update {
            it.copy(email = email, validationError = null, serverError = null)
        }
    }

    /**
     * Валидирует почту локально, затем проверяет её на сервере.
     * При успехе переходит к шагу пароля с заголовком
     * «Вход» или «Регистрация».
     */
    fun validateAndProceedEmail() {
        val currentState = _uiState.value

        if (currentState.email.isBlank()) {
            _uiState.update { it.copy(validationError = ValidationError.EmptyEmail) }
            return
        }

        when (validator.validateEmail(currentState.email)) {
            ValidationResult.Valid -> { /* proceed to server check */ }
            is ValidationResult.Invalid -> {
                _uiState.update { it.copy(validationError = ValidationError.InvalidEmail) }
                return
            }
        }

        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, validationError = null, serverError = null) }
            val result = authApiService.checkEmail(currentState.email)
            when (result) {
                is AuthResult.EmailChecked -> {
                    _uiState.update {
                        it.copy(
                            currentStep = AuthStep.Password,
                            isLogin = result.exists,
                            isLoading = false
                        )
                    }
                }
                is AuthResult.Success -> {
                    _uiState.update {
                        it.copy(
                            currentStep = AuthStep.Password,
                            isLogin = true,
                            isLoading = false
                        )
                    }
                }
                is AuthResult.Failure -> {
                    _uiState.update { it.copy(isLoading = false, serverError = ServerError.Custom(result.message)) }
                }
                AuthResult.RateLimited -> {
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            isRateLimited = true,
                            serverError = ServerError.RateLimited
                        )
                    }
                }
                AuthResult.Offline -> {
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            serverError = ServerError.Offline
                        )
                    }
                }
            }
        }
    }

    /**
     * Отправляет пароль на сервер (вход или регистрация в зависимости
     * от isLogin). При успехе сохраняет сессию и вызывает onAuthSuccess.
     */
    fun submitPassword(password: String, onAuthSuccess: () -> Unit) {
        val currentState = _uiState.value

        if (password.isBlank()) {
            _uiState.update { it.copy(validationError = ValidationError.EmptyPassword) }
            return
        }

        when (validator.validatePassword(password)) {
            ValidationResult.Valid -> { /* proceed */ }
            is ValidationResult.Invalid -> {
                _uiState.update { it.copy(validationError = ValidationError.ShortPassword) }
                return
            }
        }

        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, validationError = null, serverError = null) }
            val result = if (currentState.isLogin) {
                authApiService.login(currentState.email, password)
            } else {
                authApiService.register(currentState.email, password)
            }

            when (result) {
                is AuthResult.EmailChecked -> {
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            serverError = ServerError.Custom("Неожиданный ответ сервера")
                        )
                    }
                }
                is AuthResult.Success -> {
                    sessionRepository.saveSession(result.token)
                    _uiState.update { it.copy(isLoading = false) }
                    onAuthSuccess()
                }
                is AuthResult.Failure -> {
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            serverError = ServerError.InvalidCredentials
                        )
                    }
                }
                AuthResult.RateLimited -> {
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            isRateLimited = true,
                            serverError = ServerError.RateLimited
                        )
                    }
                }
                AuthResult.Offline -> {
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            serverError = ServerError.Offline
                        )
                    }
                }
            }
        }
    }

    /**
     * Возврат к шагу ввода почты. Введённая почта сохраняется,
     * ошибки очищаются.
     */
    fun goBack() {
        _uiState.update {
            it.copy(
                currentStep = AuthStep.Email,
                validationError = null,
                serverError = null
            )
        }
    }

    /**
     * Очищает ошибку. Вызывается при взаимодействии пользователя
     * с полем ввода.
     */
    fun clearError() {
        _uiState.update { it.copy(validationError = null, serverError = null) }
    }
}
