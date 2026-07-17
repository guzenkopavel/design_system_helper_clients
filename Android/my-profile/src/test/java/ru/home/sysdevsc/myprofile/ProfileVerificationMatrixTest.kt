package ru.home.sysdevsc.myprofile

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import ru.home.sysdevsc.myprofile.model.ProfileSnapshot
import ru.home.sysdevsc.myprofile.ui.ProfileUiState

class ProfileVerificationMatrixTest {
    @Test
    fun profileSnapshotMatchesActionAvailabilityCriteria() {
        val available = ProfileSnapshot(
            email = "user@example.com",
            completedInterviewCount = 2,
            isHistoryComplete = true,
        )
        val empty = ProfileSnapshot(
            email = "user@example.com",
            completedInterviewCount = 0,
            isHistoryComplete = true,
        )
        val incomplete = ProfileSnapshot(
            email = "user@example.com",
            completedInterviewCount = 2,
            isHistoryComplete = false,
        )

        assertTrue(available.canOpenMyInterviews)
        assertFalse(empty.canOpenMyInterviews)
        assertFalse(incomplete.canOpenMyInterviews)
    }

    @Test
    fun profileUiStateKeepsLocalizationAndRecoveryInputsExplicit() {
        val state = ProfileUiState(
            email = "user@example.com",
            completedInterviewCount = null,
            isHistoryComplete = false,
            isHistoryLoading = false,
            recoveryMessage = "Нет сетевого подключения",
            isLogoutInProgress = true,
        )

        assertEquals("user@example.com", state.email)
        assertEquals("Нет сетевого подключения", state.recoveryMessage)
        assertFalse(state.canOpenMyInterviews)
        assertTrue(state.isLogoutInProgress)
    }
}
