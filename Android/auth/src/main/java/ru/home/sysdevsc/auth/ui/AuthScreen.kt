//
//  AuthScreen.kt
//  SysDevSc
//
//  Created by Pavel Guzenko on 16.07.2026.
//  Copyright © 2026 Eltex. All rights reserved.
//

package ru.home.sysdevsc.auth.ui

import androidx.annotation.StringRes
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import ru.home.sysdevsc.auth.R

/**
 * Корневой компонуемый элемент экранов авторизации.
 * Содержит двухшаговый флоу: ввод почты и ввод пароля.
 *
 * @param uiState состояние из AuthViewModel.
 * @param onEmailChanged обработка изменения адреса почты.
 * @param onEmailSubmit обработка отправки почты (переход к паролю).
 * @param onPasswordSubmit обработка отправки пароля.
 * @param onBack обработка возврата к шагу почты.
 * @param onPasswordChanged обработка изменения текста пароля.
 */
@Composable
fun AuthScreen(
    uiState: UiState,
    onEmailChanged: (String) -> Unit,
    onEmailSubmit: () -> Unit,
    onPasswordSubmit: (String) -> Unit,
    onBack: () -> Unit,
    onPasswordChanged: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    var password by remember(uiState.currentStep, uiState.email) { mutableStateOf("") }
    val passwordFocusRequester = remember { FocusRequester() }

    Box(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
            modifier = Modifier.fillMaxWidth()
        ) {
            when (uiState.currentStep) {
                AuthStep.Email -> EmailStep(
                    email = uiState.email,
                    onEmailChanged = onEmailChanged,
                    onNext = onEmailSubmit,
                    error = uiState.validationError,
                    isLoading = uiState.isLoading,
                    isRateLimited = uiState.isRateLimited,
                    serverError = uiState.serverError
                )
                AuthStep.Password -> PasswordStep(
                    email = uiState.email,
                    isLogin = uiState.isLogin,
                    onBack = onBack,
                    password = password,
                    onPasswordChanged = {
                        password = it
                        onPasswordChanged(it)
                    },
                    onSubmit = { onPasswordSubmit(password) },
                    focusRequester = passwordFocusRequester,
                    error = uiState.validationError,
                    isLoading = uiState.isLoading,
                    isRateLimited = uiState.isRateLimited,
                    serverError = uiState.serverError
                )
            }
        }
    }
}

/**
 * Шаг ввода электронной почты.
 */
@Composable
private fun EmailStep(
    email: String,
    onEmailChanged: (String) -> Unit,
    onNext: () -> Unit,
    error: ValidationError?,
    isLoading: Boolean,
    isRateLimited: Boolean,
    serverError: ServerError?,
    modifier: Modifier = Modifier
) {
    val showFieldError = shouldShowFieldError(error, serverError)
    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        OutlinedTextField(
            value = email,
            onValueChange = onEmailChanged,
            label = { Text(stringResource(R.string.auth_hint_email)) },
            isError = showFieldError,
            supportingText = if (showFieldError) {
                { Text(getErrorMessageText(error, serverError)) }
            } else null,
            modifier = Modifier.fillMaxWidth(),
            singleLine = true
        )

        AuthActionButtons(
            isLoading = isLoading,
            isRateLimited = isRateLimited,
            buttonText = stringResource(R.string.auth_button_next),
            onClick = onNext
        )
    }
}

/**
 * Шаг ввода пароля с явным заголовком «Вход» или «Регистрация».
 */
@Composable
private fun PasswordStep(
    email: String,
    isLogin: Boolean,
    onBack: () -> Unit,
    password: String,
    onPasswordChanged: (String) -> Unit,
    onSubmit: () -> Unit,
    focusRequester: FocusRequester,
    error: ValidationError?,
    isLoading: Boolean,
    isRateLimited: Boolean,
    serverError: ServerError?,
    modifier: Modifier = Modifier
) {
    val titleRes = if (isLogin) R.string.auth_title_login else R.string.auth_title_register
    val submitRes = if (isLogin) R.string.auth_button_login else R.string.auth_button_register
    val showFieldError = shouldShowFieldError(error, serverError)
    LaunchedEffect(Unit) {
        focusRequester.requestFocus()
    }

    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Text(
            text = stringResource(titleRes),
            style = MaterialTheme.typography.headlineSmall
        )

        // Почта видима для контекста, но не редактируется
        Text(
            text = email,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        OutlinedTextField(
            value = password,
            onValueChange = onPasswordChanged,
            label = { Text(stringResource(R.string.auth_hint_password)) },
            isError = showFieldError,
            supportingText = if (showFieldError) {
                { Text(getErrorMessageText(error, serverError)) }
            } else null,
            modifier = Modifier
                .fillMaxWidth()
                .focusRequester(focusRequester),
            singleLine = true
        )

        AuthActionButtons(
            isLoading = isLoading,
            isRateLimited = isRateLimited,
            buttonText = stringResource(submitRes),
            onClick = onSubmit
        )

        TextButton(
            onClick = onBack,
            enabled = !isLoading
        ) {
            Text(stringResource(R.string.auth_button_back))
        }
    }
}

/**
 * Группа кнопок основного действия с индикатором загрузки и ошибкой сервера.
 */
@Composable
private fun AuthActionButtons(
    isLoading: Boolean,
    isRateLimited: Boolean,
    buttonText: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val loadingLabel = stringResource(R.string.auth_label_loading)
    Column(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        if (isLoading) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                CircularProgressIndicator(
                    modifier = Modifier
                        .size(24.dp)
                        .semantics { contentDescription = loadingLabel }
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = loadingLabel,
                    style = MaterialTheme.typography.bodyMedium
                )
            }
        }

        FilledTonalButton(
            onClick = onClick,
            enabled = !isLoading && !isRateLimited,
            modifier = Modifier.fillMaxWidth()
        ) {
            if (isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier
                        .size(20.dp)
                        .semantics { contentDescription = loadingLabel },
                    strokeWidth = 2.dp
                )
            } else {
                Text(buttonText)
            }
        }

        if (isRateLimited) {
            Text(
                text = stringResource(R.string.auth_error_rate_limited),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.error
            )
        }
    }
}

private fun shouldShowFieldError(error: ValidationError?, serverError: ServerError?): Boolean {
    return error != null || (serverError != null && serverError != ServerError.RateLimited)
}

/**
 * Сопоставляет тип ошибки с текстом (использует серверную ошибку при наличии).
 */
@Composable
private fun getErrorMessageText(error: ValidationError?, serverError: ServerError?): String {
    // При наличии серверной ошибки показываем её
    serverError?.let {
        return when (it) {
            is ServerError.InvalidCredentials -> stringResource(R.string.auth_error_invalid_credentials)
            is ServerError.EmailTaken -> stringResource(R.string.auth_error_email_taken)
            ServerError.RateLimited -> stringResource(R.string.auth_error_rate_limited)
            ServerError.Offline -> stringResource(R.string.auth_error_offline)
            is ServerError.Custom -> it.message
        }
    }

    // Иначе показываем ошибку локальной валидации
    return when (error) {
        ValidationError.EmptyEmail -> stringResource(R.string.auth_error_empty_email)
        ValidationError.EmptyPassword -> stringResource(R.string.auth_error_empty_password)
        ValidationError.InvalidEmail -> stringResource(R.string.auth_error_invalid_email)
        ValidationError.ShortPassword -> stringResource(R.string.auth_error_short_password)
        null -> ""
    }
}
