package ru.home.sysdevsc.appshell

data class AppShellState(
    val selectedDestination: AppShellDestination,
) {
    val selectedDestinations: List<AppShellDestination>
        get() = listOf(selectedDestination)

    fun select(destination: AppShellDestination): AppShellState =
        if (destination == selectedDestination) this else copy(selectedDestination = destination)

    companion object {
        fun initial(): AppShellState = AppShellState(AppShellDestination.Cases)
    }
}
