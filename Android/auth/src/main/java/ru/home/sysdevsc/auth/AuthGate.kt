//
//  AuthGate.kt
//  SysDevSc
//
//  Created by Pavel Guzenko on 16.07.2026.
//  Copyright © 2026 Eltex. All rights reserved.
//

package ru.home.sysdevsc.auth

import android.content.Context
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.viewmodel.compose.viewModel
import ru.home.sysdevsc.auth.data.AuthApiService
import ru.home.sysdevsc.auth.data.DefaultAuthApiService
import ru.home.sysdevsc.auth.data.EncryptedSessionRepository
import ru.home.sysdevsc.auth.data.SessionRepository
import ru.home.sysdevsc.auth.ui.AuthScreen
import ru.home.sysdevsc.auth.ui.AuthViewModel

/**
 * Корневой компонент авторизации.
 *
 * При запуске проверяет сессионный секрет через [SessionRepository]:
 * - валидная сессия — немедленно вызывает [onAuthenticated], потребитель показывает AppShell;
 * - невалидная сессия — показывает [AuthScreen] с шагом почты;
 * - успешная авторизация в [AuthScreen] сохраняет сессию и вызывает [onAuthenticated].
 *
 * Остаётся публичной границей модуля `:auth` без раскрытия внутренней логики
 * и без прямой зависимости от `:app-shell`.
 *
 * @param onAuthenticated обратный вызов при успешной проверке сессии.
 * @param authApiService сетевой сервис авторизации; по умолчанию создаётся [DefaultAuthApiService]
 *                       с базовым URL из build config.
 * @param sessionRepository хранилище сессии; по умолчанию создаётся [EncryptedSessionRepository].
 * @param modifier модификатор компоновки.
 */
@Composable
fun AuthGate(
    onAuthenticated: () -> Unit,
    authApiService: AuthApiService? = null,
    sessionRepository: SessionRepository? = null,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val repository = remember(sessionRepository, context) {
        sessionRepository ?: EncryptedSessionRepository(context)
    }
    val apiService = remember(authApiService, context) {
        authApiService ?: createDefaultApiService(context)
    }

    var authState: AuthState by remember { mutableStateOf(AuthState.Idle) }
    var isCheckingSession by remember { mutableStateOf(true) }

    val viewModel: AuthViewModel = viewModel(
        key = "AuthViewModel:${System.identityHashCode(apiService)}:${System.identityHashCode(repository)}",
        factory = AuthViewModelFactory(apiService, repository)
    )

    // Проверка сессии при первом запуске
    LaunchedEffect(repository) {
        val session = repository.getSession()
        if (session != null && session.isNotEmpty()) {
            authState = AuthState.Authenticated
            isCheckingSession = false
            onAuthenticated()
        } else {
            authState = AuthState.Idle
            isCheckingSession = false
        }
    }

    when (authState) {
        is AuthState.Authenticated -> {
            // Потребитель уже получил onAuthenticated и показывает AppShell
            // Этот блок не должен отображаться — onAuthenticated вызывается асинхронно
        }
        else -> {
            if (!isCheckingSession) {
                AuthScreenWithViewModel(
                    viewModel = viewModel,
                    onAuthSuccess = {
                        authState = AuthState.Authenticated
                        onAuthenticated()
                    },
                    modifier = modifier
                )
            }
        }
    }
}

/**
 * Внутренний обёрточный компонент, связывающий AuthViewModel с AuthScreen.
 * Не является частью публичного API модуля.
 */
@Composable
private fun AuthScreenWithViewModel(
    viewModel: AuthViewModel,
    onAuthSuccess: () -> Unit,
    modifier: Modifier = Modifier
) {
    val uiState by viewModel.uiState.collectAsState()

    AuthScreen(
        uiState = uiState,
        onEmailChanged = viewModel::onEmailChanged,
        onEmailSubmit = viewModel::validateAndProceedEmail,
        onPasswordSubmit = { password ->
            viewModel.submitPassword(password, onAuthSuccess)
        },
        onBack = viewModel::goBack,
        onPasswordChanged = { /* пароль хранится локально в AuthScreen */ },
        modifier = modifier
    )
}

/**
 * Фабрика для создания AuthViewModel с внедрёнными зависимостями.
 */
class AuthViewModelFactory(
    private val authApiService: AuthApiService,
    private val sessionRepository: SessionRepository
) : androidx.lifecycle.ViewModelProvider.Factory {
    @Suppress("UNCHECKED_CAST")
    override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {
        return if (modelClass.isAssignableFrom(AuthViewModel::class.java)) {
            AuthViewModel(authApiService, sessionRepository) as T
        } else {
            throw IllegalArgumentException("Unknown ViewModel class")
        }
    }
}

/**
 * Создаёт DefaultAuthApiService с базовым URL из ресурсов приложения.
 * В production URL подставляется через app resource auth_api_base_url.
 */
private fun createDefaultApiService(context: Context): AuthApiService {
    // Базовый URL берётся из ресурсов — внешний параметр окружения
    val resourceId = context.resources.getIdentifier("auth_api_base_url", "string", context.packageName)
    val baseUrl = if (resourceId != 0) {
        context.getString(resourceId).trim().takeIf { it.isNotEmpty() }
    } else {
        null
    } ?: "https://89.125.1.21.nip.io/"
    return DefaultAuthApiService(baseUrl = baseUrl)
}
