package ru.home.sysdevsc

import androidx.activity.compose.setContent
import androidx.compose.material3.Text
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import org.junit.Rule
import org.junit.Test
import ru.home.sysdevsc.appshell.AppShell
import ru.home.sysdevsc.appshell.AppShellState
import ru.home.sysdevsc.myprofile.ui.ProfileScreen
import ru.home.sysdevsc.myprofile.ui.ProfileUiState

class MyProfileIntegrationTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun profileDestinationRendersInjectedProfileContent() {
        composeRule.runOnUiThread {
            composeRule.activity.setContent {
                var state by remember { mutableStateOf(AppShellState.initial()) }
                AppShell(
                    state = state,
                    onDestinationSelected = { state = state.select(it) },
                    profileContent = { Text("Профиль подключён") },
                )
            }
        }

        composeRule.onNodeWithTag("app_shell_destination_profile").performClick()
        composeRule.onNodeWithText("Профиль подключён").assertIsDisplayed()
    }

    @Test
    fun profileDestinationKeepsBottomNavigationWhileShowingProfileScreen() {
        composeRule.runOnUiThread {
            composeRule.activity.setContent {
                var state by remember { mutableStateOf(AppShellState.initial()) }
                AppShell(
                    state = state,
                    onDestinationSelected = { state = state.select(it) },
                    profileContent = {
                        ProfileScreen(
                            state = ProfileUiState(
                                email = "user@example.com",
                                completedInterviewCount = 2,
                                isHistoryComplete = true,
                                isHistoryLoading = false,
                                recoveryMessage = null,
                                isLogoutInProgress = false,
                            ),
                            onMyInterviewsClick = {},
                            onLogoutClick = {},
                        )
                    },
                )
            }
        }

        composeRule.onNodeWithTag("app_shell_destination_profile").performClick()

        composeRule.onNodeWithText("user@example.com").assertIsDisplayed()
        composeRule.onNodeWithText("Мои интервью").assertIsDisplayed()
        composeRule.onNodeWithText("Выход").assertIsDisplayed()
        composeRule.onNodeWithTag("app_shell_destination_cases").assertIsDisplayed()
    }
}
