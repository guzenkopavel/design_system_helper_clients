package ru.home.sysdevsc

import androidx.activity.compose.setContent
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assert
import androidx.compose.ui.test.hasStateDescription
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onFirst
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import org.junit.Rule
import org.junit.Test
import ru.home.sysdevsc.appshell.AppShell
import ru.home.sysdevsc.appshell.AppShellState

class AppShellIntegrationTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun launchShowsApprovedAppShellDestinations() {
        setAppShellContent()

        composeRule.onAllNodesWithText("Кейсы").onFirst().assertIsDisplayed()
        composeRule.onAllNodesWithText("Знания").onFirst().assertIsDisplayed()
        composeRule.onAllNodesWithText("Профиль").onFirst().assertIsDisplayed()
    }

    @Test
    fun launchSelectsCasesAndAllowsDestinationTransitions() {
        setAppShellContent()

        composeRule
            .onNodeWithTag("app_shell_destination_cases")
            .assert(hasStateDescription("Выбрано"))

        composeRule
            .onNodeWithTag("app_shell_destination_profile")
            .performClick()
            .assert(hasStateDescription("Выбрано"))

        composeRule
            .onNodeWithText("Нейтральная поверхность раздела «Профиль».")
            .assertIsDisplayed()
    }

    private fun setAppShellContent() {
        composeRule.runOnUiThread {
            composeRule.activity.setContent {
                var state by remember { mutableStateOf(AppShellState.initial()) }
                AppShell(
                    state = state,
                    onDestinationSelected = { destination ->
                        state = state.select(destination)
                    },
                )
            }
        }
        composeRule.waitForIdle()
    }
}
