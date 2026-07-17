package ru.home.sysdevsc

import androidx.activity.compose.setContent
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

class MyProfileRuntimeTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun appShellKeepsNavigationAroundInjectedProfileRuntimeContent() {
        composeRule.runOnUiThread {
            composeRule.activity.setContent {
                var state by remember { mutableStateOf(AppShellState.initial()) }
                AppShell(
                    state = state,
                    onDestinationSelected = { state = state.select(it) },
                    profileContent = {
                        ProfileScreen(
                            state = ProfileUiState(
                                email = "runtime@example.com",
                                completedInterviewCount = 3,
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

        composeRule.onNodeWithText("runtime@example.com").assertIsDisplayed()
        composeRule.onNodeWithText("Мои интервью").assertIsDisplayed()
        composeRule.onNodeWithTag("app_shell_destination_cases").assertIsDisplayed()
    }
}
