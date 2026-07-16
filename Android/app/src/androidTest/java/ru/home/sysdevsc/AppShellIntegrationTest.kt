package ru.home.sysdevsc

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

class AppShellIntegrationTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun launchShowsApprovedAppShellDestinations() {
        composeRule.onAllNodesWithText("Кейсы").onFirst().assertIsDisplayed()
        composeRule.onAllNodesWithText("Знания").onFirst().assertIsDisplayed()
        composeRule.onAllNodesWithText("Профиль").onFirst().assertIsDisplayed()
    }

    @Test
    fun launchSelectsCasesAndAllowsDestinationTransitions() {
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
}
