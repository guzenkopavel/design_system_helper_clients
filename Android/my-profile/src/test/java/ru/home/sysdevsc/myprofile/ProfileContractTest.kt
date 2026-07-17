package ru.home.sysdevsc.myprofile

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ProfileContractTest {
    @Test
    fun readyStateEnablesMyInterviewsOnlyAfterCompletePositiveCount() {
        val incomplete = ProfileState.Ready(
            email = "user@example.com",
            completedInterviewCount = 3,
            isHistoryComplete = false,
        )
        val empty = ProfileState.Ready(
            email = "user@example.com",
            completedInterviewCount = 0,
            isHistoryComplete = true,
        )
        val available = ProfileState.Ready(
            email = "user@example.com",
            completedInterviewCount = 3,
            isHistoryComplete = true,
        )

        assertFalse(incomplete.canOpenMyInterviews)
        assertFalse(empty.canOpenMyInterviews)
        assertTrue(available.canOpenMyInterviews)
    }

    @Test
    fun stateContractKeepsInvalidSessionExplicit() {
        val state: ProfileState = ProfileState.InvalidSession

        assertTrue(state is ProfileState.InvalidSession)
    }
}
