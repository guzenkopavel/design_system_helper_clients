package ru.home.sysdevsc.appshell

private fun assertEquals(expected: Any, actual: Any) {
    check(expected == actual) {
        "Expected <$expected>, actual <$actual>"
    }
}

private fun assertSame(expected: Any, actual: Any) {
    check(expected === actual) {
        "Expected same instance <$expected>, actual <$actual>"
    }
}

class AppShellStateTest {
    fun testDestinationsKeepApprovedOrderAndLabels() {
        assertEquals(
            listOf("Кейсы", "Знания", "Профиль"),
            AppShellDestination.entries.map { it.label }
        )
    }

    fun testInitialStateSelectsCasesOnly() {
        val state = AppShellState.initial()

        assertSame(AppShellDestination.Cases, state.selectedDestination)
        assertEquals(1, state.selectedDestinations.count())
        assertEquals(listOf(AppShellDestination.Cases), state.selectedDestinations)
    }

    fun testSelectingEachDestinationReplacesSelection() {
        AppShellDestination.entries.forEach { destination ->
            val state = AppShellState.initial().select(destination)

            assertSame(destination, state.selectedDestination)
            assertEquals(listOf(destination), state.selectedDestinations)
        }
    }

    fun testSelectingCurrentDestinationKeepsStateStable() {
        val state = AppShellState.initial()

        assertSame(state, state.select(AppShellDestination.Cases))
    }

    fun testDestinationContractHasNoFourthState() {
        AppShellDestination.entries.forEach { destination ->
            when (destination) {
                AppShellDestination.Cases -> assertEquals("Кейсы", destination.label)
                AppShellDestination.Knowledge -> assertEquals("Знания", destination.label)
                AppShellDestination.Profile -> assertEquals("Профиль", destination.label)
            }
        }
    }
}

fun main() {
    val test = AppShellStateTest()

    test.testDestinationsKeepApprovedOrderAndLabels()
    test.testInitialStateSelectsCasesOnly()
    test.testSelectingEachDestinationReplacesSelection()
    test.testSelectingCurrentDestinationKeepsStateStable()
    test.testDestinationContractHasNoFourthState()
}
