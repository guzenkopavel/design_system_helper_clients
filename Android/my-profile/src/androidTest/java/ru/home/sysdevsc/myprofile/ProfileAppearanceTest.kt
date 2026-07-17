package ru.home.sysdevsc.myprofile

import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import org.junit.Rule
import org.junit.Test
import ru.home.sysdevsc.myprofile.ui.ProfileScreen
import ru.home.sysdevsc.myprofile.ui.ProfileUiState

class ProfileAppearanceTest {
    @get:Rule
    val composeRule = createComposeRule()

    @Test
    fun materialProfileAppearanceExposesCoreSemantics() {
        composeRule.setContent {
            MaterialTheme {
                ProfileScreen(
                    state = ProfileUiState(
                        email = "user@example.com",
                        completedInterviewCount = 1,
                        isHistoryComplete = true,
                        isHistoryLoading = false,
                        recoveryMessage = null,
                        isLogoutInProgress = false,
                    ),
                    onMyInterviewsClick = {},
                    onLogoutClick = {},
                )
            }
        }

        composeRule.onNodeWithTag("my_profile_content").assertIsDisplayed()
        composeRule.onNodeWithText("user@example.com").assertIsDisplayed()
        composeRule.onNodeWithText("Мои интервью").assertIsDisplayed()
        composeRule.onNodeWithText("Выход").assertIsDisplayed()
    }
}
