package ru.home.sysdevsc

import androidx.activity.compose.setContent
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.assert
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsFocused
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.hasClickAction
import androidx.compose.ui.test.hasSetTextAction
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTextInput
import androidx.compose.ui.unit.Density
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import ru.home.sysdevsc.auth.ui.AuthScreen
import ru.home.sysdevsc.auth.ui.AuthStep
import ru.home.sysdevsc.auth.ui.UiState
import ru.home.sysdevsc.auth.ui.ValidationError
import ru.home.sysdevsc.ui.theme.SysDevScTheme

class AuthAccessibilityTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun visibleLabelsAreExposedAsAccessibleFieldNames() {
        setActivityContent {
            SysDevScTheme(dynamicColor = false) {
                StatelessAuthScreen(UiState())
            }
        }

        composeRule
            .onNode(hasSetTextAction())
            .assert(hasText("Электронная почта"))
        composeRule
            .onNode(hasText("Далее") and hasClickAction())
            .assert(
                SemanticsMatcher.expectValue(
                    SemanticsProperties.Role,
                    Role.Button,
                ),
            )
    }

    @Test
    fun passwordAndActionsExposeVisibleAccessibleNamesAndButtonRoles() {
        setActivityContent {
            SysDevScTheme(dynamicColor = false) {
                StatelessAuthScreen(
                    UiState(
                        currentStep = AuthStep.Password,
                        email = TEST_EMAIL,
                        isLogin = true,
                    ),
                )
            }
        }

        composeRule
            .onNode(hasSetTextAction())
            .assert(hasText("Пароль"))
        listOf("Войти", "Назад").forEach { accessibleName ->
            composeRule
                .onNode(hasText(accessibleName) and hasClickAction())
                .assert(
                    SemanticsMatcher.expectValue(
                        SemanticsProperties.Role,
                        Role.Button,
                    ),
                )
        }
    }

    @Test
    fun registrationPasswordStepShowsRegistrationTitle() {
        setActivityContent {
            SysDevScTheme(dynamicColor = false) {
                StatelessAuthScreen(
                    UiState(
                        currentStep = AuthStep.Password,
                        email = TEST_EMAIL,
                        isLogin = false,
                    ),
                )
            }
        }

        composeRule.onNodeWithText("Регистрация").assertIsDisplayed()
        composeRule.onNodeWithText(TEST_EMAIL).assertIsDisplayed()
    }

    @Test
    fun passwordFieldReceivesLogicalFocusAfterStepChange() {
        setActivityContent {
            StatefulAuthScreen()
        }

        composeRule.onNode(hasSetTextAction()).performTextInput(TEST_EMAIL)
        composeRule.onNodeWithText("Далее").performClick()

        composeRule.onNode(hasSetTextAction()).assertIsFocused()
        composeRule.onNodeWithText("Вход").assertIsDisplayed()
    }

    @Test
    fun validationErrorHasTextAndAssistiveErrorSemantics() {
        setActivityContent {
            StatelessAuthScreen(
                UiState(validationError = ValidationError.EmptyEmail),
            )
        }

        composeRule.onNodeWithText("Введите адрес электронной почты").assertIsDisplayed()
        composeRule
            .onNode(hasSetTextAction())
            .assert(SemanticsMatcher.keyIsDefined(SemanticsProperties.Error))
    }

    @Test
    fun loadingAndRateLimitHaveNonColorCues() {
        setActivityContent {
            StatelessAuthScreen(UiState(isLoading = true))
        }
        composeRule
            .onAllNodesWithContentDescription("Проверка…")
            .assertCountEquals(2)
        composeRule.onNodeWithText("Проверка…").assertIsDisplayed()

        setActivityContent {
            StatelessAuthScreen(UiState(isRateLimited = true))
        }
        composeRule
            .onNodeWithText("Слишком много попыток. Повторите позже.")
            .assertIsDisplayed()
        composeRule.onNodeWithText("Далее").assertIsNotEnabled()
    }

    @Test
    fun contentRemainsDiscoverableAtTwoHundredPercentFontScale() {
        setActivityContent {
            val baseDensity = LocalDensity.current
            CompositionLocalProvider(
                LocalDensity provides Density(baseDensity.density, fontScale = 2f),
            ) {
                StatelessAuthScreen(UiState())
            }
        }

        composeRule.onNodeWithText("Электронная почта").assertIsDisplayed()
        composeRule.onNodeWithText("Далее").assertIsDisplayed()
    }

    @Test
    fun lightAndDarkMaterialRolesHaveAccessibleOnColors() {
        val light = captureThemeColors(darkTheme = false, dynamicColor = false)
        val dark = captureThemeColors(darkTheme = true, dynamicColor = false)

        assertTrue(contrastRatio(light.primary, light.onPrimary) >= MIN_TEXT_CONTRAST)
        assertTrue(contrastRatio(dark.primary, dark.onPrimary) >= MIN_TEXT_CONTRAST)
        assertTrue(
            contrastRatio(light.secondaryContainer, light.onSecondaryContainer) >= MIN_TEXT_CONTRAST,
        )
        assertTrue(
            contrastRatio(dark.secondaryContainer, dark.onSecondaryContainer) >= MIN_TEXT_CONTRAST,
        )
        assertTrue(contrastRatio(light.error, light.onError) >= MIN_TEXT_CONTRAST)
        assertTrue(contrastRatio(dark.error, dark.onError) >= MIN_TEXT_CONTRAST)
        assertTrue(contrastRatio(light.surface, light.onSurface) >= MIN_TEXT_CONTRAST)
        assertTrue(contrastRatio(dark.surface, dark.onSurface) >= MIN_TEXT_CONTRAST)
    }

    @Test
    fun defaultThemeKeepsDynamicColorDisabledAndUsesSoftBlueFallback() {
        val light = captureThemeColors(darkTheme = false)
        val dark = captureThemeColors(darkTheme = true)

        assertEquals(SOFT_BLUE_LIGHT_PRIMARY, light.primary)
        assertEquals(SOFT_BLUE_DARK_PRIMARY, dark.primary)
    }

    private fun captureThemeColors(
        darkTheme: Boolean,
        dynamicColor: Boolean? = null,
    ): ThemeColors {
        lateinit var result: ThemeColors
        setActivityContent {
            val themedContent: @Composable () -> Unit = {
                result = ThemeColors(
                    primary = MaterialTheme.colorScheme.primary,
                    onPrimary = MaterialTheme.colorScheme.onPrimary,
                    secondaryContainer = MaterialTheme.colorScheme.secondaryContainer,
                    onSecondaryContainer = MaterialTheme.colorScheme.onSecondaryContainer,
                    error = MaterialTheme.colorScheme.error,
                    onError = MaterialTheme.colorScheme.onError,
                    surface = MaterialTheme.colorScheme.surface,
                    onSurface = MaterialTheme.colorScheme.onSurface,
                )
            }
            if (dynamicColor == null) {
                SysDevScTheme(darkTheme = darkTheme, content = themedContent)
            } else {
                SysDevScTheme(
                    darkTheme = darkTheme,
                    dynamicColor = dynamicColor,
                    content = themedContent,
                )
            }
        }
        composeRule.runOnIdle { }
        return result
    }

    @Composable
    private fun StatefulAuthScreen() {
        var state by remember { mutableStateOf(UiState()) }
        SysDevScTheme(dynamicColor = false) {
            AuthScreen(
                uiState = state,
                onEmailChanged = { state = state.copy(email = it) },
                onEmailSubmit = {
                    state = state.copy(currentStep = AuthStep.Password, isLogin = true)
                },
                onPasswordSubmit = { },
                onBack = { state = state.copy(currentStep = AuthStep.Email) },
                onPasswordChanged = { },
            )
        }
    }

    @Composable
    private fun StatelessAuthScreen(state: UiState) {
        AuthScreen(
            uiState = state,
            onEmailChanged = { },
            onEmailSubmit = { },
            onPasswordSubmit = { },
            onBack = { },
            onPasswordChanged = { },
        )
    }

    private fun setActivityContent(content: @Composable () -> Unit) {
        composeRule.runOnUiThread {
            composeRule.activity.setContent(content = content)
        }
        composeRule.waitForIdle()
    }

    private fun contrastRatio(first: Color, second: Color): Float {
        val lighter = maxOf(first.luminance(), second.luminance())
        val darker = minOf(first.luminance(), second.luminance())
        return (lighter + 0.05f) / (darker + 0.05f)
    }

    private data class ThemeColors(
        val primary: Color,
        val onPrimary: Color,
        val secondaryContainer: Color,
        val onSecondaryContainer: Color,
        val error: Color,
        val onError: Color,
        val surface: Color,
        val onSurface: Color,
    )

    private companion object {
        const val TEST_EMAIL = "person@example.com"
        const val MIN_TEXT_CONTRAST = 4.5f
        val SOFT_BLUE_LIGHT_PRIMARY = Color(0xFF2F5F9F)
        val SOFT_BLUE_DARK_PRIMARY = Color(0xFFA8C8FF)
    }
}
