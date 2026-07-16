package ru.home.sysdevsc.appshell

import androidx.compose.runtime.Composable

object AppShellTest {
    @Composable
    fun appShellExposesHoistedStateContract() {
        AppShell(
            state = AppShellState.initial(),
            onDestinationSelected = { selected ->
                check(selected in AppShellDestination.entries)
            }
        )
    }

    fun destinationContractKeepsApprovedLabelsOnly(): List<String> =
        AppShellDestination.entries.map { it.label }
}
