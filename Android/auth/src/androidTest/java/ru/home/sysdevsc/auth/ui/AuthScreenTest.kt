//
//  AuthScreenTest.kt
//  SysDevSc
//
//  Created by Pavel Guzenko on 16.07.2026.
//  Copyright © 2026 Eltex. All rights reserved.
//

package ru.home.sysdevsc.auth.ui

import androidx.annotation.StringRes
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import ru.home.sysdevsc.auth.R

/**
 * Compose UI-тесты экранов авторизации.
 * Проверяют отображение полей, кнопок, ошибок, загрузки и переходов между шагами.
 */
class AuthScreenTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    private var capturedPassword = ""

    private fun createState(
        currentStep: AuthStep = AuthStep.Email,
        email: String = "",
        isLogin: Boolean = true,
        isLoading: Boolean = false,
        validationError: ValidationError? = null,
        serverError: ServerError? = null,
        isRateLimited: Boolean = false
    ): UiState {
        return UiState(
            currentStep = currentStep,
            email = email,
            isLogin = isLogin,
            isLoading = isLoading,
            validationError = validationError,
            serverError = serverError,
            isRateLimited = isRateLimited
        )
    }

    private fun launchAuthScreen(uiState: UiState) {
        composeTestRule.setContent {
            AuthScreen(
                uiState = uiState,
                onEmailChanged = { },
                onEmailSubmit = { },
                onPasswordSubmit = { },
                onBack = { },
                onPasswordChanged = { capturedPassword = it }
            )
        }
    }

    @Before
    fun setup() {
        capturedPassword = ""
    }

    private fun stringResource(@StringRes resId: Int): String {
        return InstrumentationRegistry.getInstrumentation().targetContext.getString(resId)
    }

    @Test
    fun emailStep_showsEmailField() {
        val state = createState()
        launchAuthScreen(state)

        composeTestRule.onNodeWithText(
            stringResource(R.string.auth_hint_email)
        ).assertExists()
    }

    @Test
    fun emailStep_showsNextButton() {
        val state = createState()
        launchAuthScreen(state)

        composeTestRule.onNodeWithText(
            stringResource(R.string.auth_button_next)
        ).assertExists()
    }

    @Test
    fun emailStep_showsEmptyEmailError() {
        val state = createState(
            validationError = ValidationError.EmptyEmail
        )
        launchAuthScreen(state)

        composeTestRule.onNodeWithText(
            stringResource(R.string.auth_error_empty_email)
        ).assertExists()
    }

    @Test
    fun emailStep_showsInvalidEmailError() {
        val state = createState(
            validationError = ValidationError.InvalidEmail
        )
        launchAuthScreen(state)

        composeTestRule.onNodeWithText(
            stringResource(R.string.auth_error_invalid_email)
        ).assertExists()
    }

    @Test
    fun passwordStep_showsLoginTitle() {
        val state = createState(
            currentStep = AuthStep.Password,
            email = "test@example.com",
            isLogin = true
        )
        launchAuthScreen(state)

        composeTestRule.onNodeWithText(
            stringResource(R.string.auth_title_login)
        ).assertExists()
    }

    @Test
    fun passwordStep_showsRegisterTitle() {
        val state = createState(
            currentStep = AuthStep.Password,
            email = "new@example.com",
            isLogin = false
        )
        launchAuthScreen(state)

        composeTestRule.onNodeWithText(
            stringResource(R.string.auth_title_register)
        ).assertExists()
    }

    @Test
    fun passwordStep_showsPasswordField() {
        val state = createState(
            currentStep = AuthStep.Password,
            email = "test@example.com"
        )
        launchAuthScreen(state)

        composeTestRule.onNodeWithText(
            stringResource(R.string.auth_hint_password)
        ).assertExists()
    }

    @Test
    fun passwordStep_showsSubmitButton() {
        val state = createState(
            currentStep = AuthStep.Password,
            email = "test@example.com",
            isLogin = true
        )
        launchAuthScreen(state)

        composeTestRule.onNodeWithText(
            stringResource(R.string.auth_button_login)
        ).assertExists()
    }

    @Test
    fun passwordStep_showsRegisterButton_forRegistration() {
        val state = createState(
            currentStep = AuthStep.Password,
            email = "test@example.com",
            isLogin = false
        )
        launchAuthScreen(state)

        composeTestRule.onNodeWithText(
            stringResource(R.string.auth_button_register)
        ).assertExists()
    }

    @Test
    fun passwordStep_showsBackButton() {
        val state = createState(
            currentStep = AuthStep.Password,
            email = "test@example.com"
        )
        launchAuthScreen(state)

        composeTestRule.onNodeWithText(
            stringResource(R.string.auth_button_back)
        ).assertExists()
    }

    @Test
    fun passwordStep_showsEmailForContext() {
        val email = "test@example.com"
        val state = createState(
            currentStep = AuthStep.Password,
            email = email
        )
        launchAuthScreen(state)

        composeTestRule.onNodeWithText(email).assertExists()
    }

    @Test
    fun passwordStep_showsEmptyPasswordError() {
        val state = createState(
            currentStep = AuthStep.Password,
            email = "test@example.com",
            validationError = ValidationError.EmptyPassword
        )
        launchAuthScreen(state)

        composeTestRule.onNodeWithText(
            stringResource(R.string.auth_error_empty_password)
        ).assertExists()
    }

    @Test
    fun passwordStep_showsShortPasswordError() {
        val state = createState(
            currentStep = AuthStep.Password,
            email = "test@example.com",
            validationError = ValidationError.ShortPassword
        )
        launchAuthScreen(state)

        composeTestRule.onNodeWithText(
            stringResource(R.string.auth_error_short_password)
        ).assertExists()
    }

    @Test
    fun passwordStep_showsInvalidCredentialsError() {
        val state = createState(
            currentStep = AuthStep.Password,
            email = "test@example.com",
            serverError = ServerError.InvalidCredentials
        )
        launchAuthScreen(state)

        composeTestRule.onNodeWithText(
            stringResource(R.string.auth_error_invalid_credentials)
        ).assertExists()
    }

    @Test
    fun passwordStep_showsOfflineError() {
        val state = createState(
            currentStep = AuthStep.Password,
            email = "test@example.com",
            serverError = ServerError.Offline
        )
        launchAuthScreen(state)

        composeTestRule.onNodeWithText(
            stringResource(R.string.auth_error_offline)
        ).assertExists()
    }

    @Test
    fun passwordStep_showsRateLimitedError() {
        val state = createState(
            currentStep = AuthStep.Password,
            email = "test@example.com",
            isRateLimited = true,
            serverError = ServerError.RateLimited
        )
        launchAuthScreen(state)

        composeTestRule.onNodeWithText(
            stringResource(R.string.auth_error_rate_limited)
        ).assertExists()
    }

    @Test
    fun emailStep_showsLoadingIndicator() {
        val state = createState(isLoading = true)
        launchAuthScreen(state)

        composeTestRule.onAllNodesWithContentDescription(
            stringResource(R.string.auth_label_loading)
        ).assertCountEquals(2)
    }

    @Test
    fun passwordStep_showsLoadingIndicator() {
        val state = createState(
            currentStep = AuthStep.Password,
            email = "test@example.com",
            isLoading = true
        )
        launchAuthScreen(state)

        composeTestRule.onAllNodesWithContentDescription(
            stringResource(R.string.auth_label_loading)
        ).assertCountEquals(2)
    }

    @Test
    fun backTransition_returnsToEmailStep() {
        var currentStep by mutableStateOf(AuthStep.Password)
        val email = "test@example.com"

        composeTestRule.setContent {
            AuthScreen(
                uiState = UiState(
                    currentStep = currentStep,
                    email = email
                ),
                onEmailChanged = { },
                onEmailSubmit = { },
                onPasswordSubmit = { },
                onBack = { currentStep = AuthStep.Email },
                onPasswordChanged = { }
            )
        }

        // На шаге пароля
        composeTestRule.onNodeWithText(
            stringResource(R.string.auth_title_login)
        ).assertExists()

        // Нажимаем «Назад»
        composeTestRule.onNodeWithText(
            stringResource(R.string.auth_button_back)
        ).performClick()

        // Заголовок входа исчезает (мы на шаге почты)
        composeTestRule.onNodeWithText(
            stringResource(R.string.auth_title_login)
        ).assertDoesNotExist()

        // Поле почты видимо
        composeTestRule.onNodeWithText(
            stringResource(R.string.auth_hint_email)
        ).assertExists()
    }

    @Test
    fun emailField_hasAccessibilityLabel() {
        val state = createState()
        launchAuthScreen(state)

        composeTestRule.onNode(hasSetTextAction() and hasText(
            stringResource(R.string.auth_hint_email)
        )).assertExists()
    }

    @Test
    fun passwordField_hasAccessibilityLabel() {
        val state = createState(
            currentStep = AuthStep.Password,
            email = "test@example.com"
        )
        launchAuthScreen(state)

        composeTestRule.onNode(hasSetTextAction() and hasText(
            stringResource(R.string.auth_hint_password)
        )).assertExists()
    }

    @Test
    fun emailStep_nextButtonDisabled_whenRateLimited() {
        val state = createState(isRateLimited = true)
        launchAuthScreen(state)

        composeTestRule.onNodeWithText(
            stringResource(R.string.auth_button_next)
        ).assertIsNotEnabled()
    }

    @Test
    fun passwordStep_submitButtonDisabled_whenRateLimited() {
        val state = createState(
            currentStep = AuthStep.Password,
            email = "test@example.com",
            isRateLimited = true
        )
        launchAuthScreen(state)

        composeTestRule.onNodeWithText(
            stringResource(R.string.auth_button_login)
        ).assertIsNotEnabled()
    }

    @Test
    fun emailStep_showsOfflineError() {
        val state = createState(serverError = ServerError.Offline)
        launchAuthScreen(state)

        composeTestRule.onNodeWithText(
            stringResource(R.string.auth_error_offline)
        ).assertExists()
    }
}
