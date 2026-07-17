package ru.home.sysdevsc.myprofile.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.SnackbarHostState
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.hasContentDescription
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

class ProfileScreenTest {
    @get:Rule
    val composeRule = createComposeRule()

    @Test
    fun readyProfileShowsEmailAndActions() {
        composeRule.setContent {
            MaterialTheme {
                ProfileScreen(
                    state = readyState(count = 4),
                    onMyInterviewsClick = {},
                    onLogoutClick = {},
                )
            }
        }

        composeRule.onNodeWithText("user@example.com").assertIsDisplayed()
        composeRule.onNode(hasContentDescription("Текущий профиль: user@example.com"))
            .assertIsDisplayed()
        composeRule.onNodeWithText("Мои интервью").assertIsDisplayed()
        composeRule.onNodeWithText("Выход").assertIsDisplayed()
        composeRule.onNodeWithTag("my_profile_my_interviews").assertIsEnabled()
    }

    @Test
    fun myInterviewsIsVisibleButDisabledWhenHistoryIsUnknownOrEmpty() {
        composeRule.setContent {
            MaterialTheme {
                ProfileScreen(
                    state = readyState(count = 0),
                    onMyInterviewsClick = {},
                    onLogoutClick = {},
                )
            }
        }

        composeRule.onNodeWithTag("my_profile_my_interviews").assertIsNotEnabled()
        composeRule.onNodeWithText("Интервью пока нет").assertIsDisplayed()
    }

    @Test
    fun activeMyInterviewsShowsCountFeedbackWithoutNavigationEvent() {
        var clickCount = 0
        val snackbarHostState = SnackbarHostState()
        composeRule.setContent {
            MaterialTheme {
                ProfileScreen(
                    state = readyState(count = 7),
                    onMyInterviewsClick = { clickCount += 1 },
                    onLogoutClick = {},
                    snackbarHostState = snackbarHostState,
                )
            }
        }

        composeRule.onNodeWithTag("my_profile_my_interviews").performClick()
        composeRule.waitForIdle()

        assertEquals(1, clickCount)
        composeRule.onNodeWithText("Интервью: 7").assertIsDisplayed()
        composeRule.onNodeWithText("user@example.com").assertIsDisplayed()
    }

    @Test
    fun logoutBusyStateDisablesRepeatedLogoutAndKeepsRecoveryMessageVisible() {
        composeRule.setContent {
            MaterialTheme {
                ProfileScreen(
                    state = readyState(
                        count = null,
                        isHistoryComplete = false,
                        recoveryMessage = "Нет сетевого подключения",
                        isLogoutInProgress = true,
                    ),
                    onMyInterviewsClick = {},
                    onLogoutClick = {},
                )
            }
        }

        composeRule.onNodeWithText("Нет сетевого подключения").assertIsDisplayed()
        composeRule.onNodeWithTag("my_profile_logout").assertIsNotEnabled()
        composeRule.onNodeWithTag("my_profile_my_interviews").assertIsNotEnabled()
    }

    private fun readyState(
        count: Int?,
        isHistoryComplete: Boolean = true,
        recoveryMessage: String? = null,
        isLogoutInProgress: Boolean = false,
    ): ProfileUiState =
        ProfileUiState(
            email = "user@example.com",
            completedInterviewCount = count,
            isHistoryComplete = isHistoryComplete,
            isHistoryLoading = false,
            recoveryMessage = recoveryMessage,
            isLogoutInProgress = isLogoutInProgress,
        )
}
