package ru.home.sysdevsc.appshell

import junit.framework.TestCase

class ProfileContentSlotTest : TestCase() {
    fun testProfileDestinationRemainsThePublicSlotOwner() {
        val state = AppShellState.initial().select(AppShellDestination.Profile)

        assertEquals(AppShellDestination.Profile, state.selectedDestination)
        assertEquals("Профиль", state.selectedDestination.label)
    }
}
