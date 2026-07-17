package ru.home.sysdevsc.myprofile.data

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.async
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Test
import ru.home.sysdevsc.myprofile.model.InterviewHistoryPage
import ru.home.sysdevsc.myprofile.model.LogoutResult
import ru.home.sysdevsc.myprofile.model.ProfileFailure
import ru.home.sysdevsc.myprofile.model.ProfileIdentity
import ru.home.sysdevsc.myprofile.model.ProfileLoadResult

@OptIn(ExperimentalCoroutinesApi::class)
class DefaultProfileRepositoryTest {
    private val dispatcher = StandardTestDispatcher()

    @Test
    fun loadProfileLoadsHistoryUntilTerminalPage() = runTest(dispatcher) {
        val remote = FakeProfileRemoteDataSource(
            historyPages = mutableMapOf(
                0 to RemoteResult.Success(InterviewHistoryPage(2, hasMore = true, nextPage = 1)),
                1 to RemoteResult.Success(InterviewHistoryPage(3, hasMore = false, nextPage = null)),
            )
        )
        val repository = repository(remote)

        val result = repository.loadProfile()

        assertEquals(listOf(0, 1), remote.requestedHistoryPages)
        val loaded = result as ProfileLoadResult.Loaded
        assertEquals("user@example.com", loaded.snapshot.email)
        assertEquals(5, loaded.snapshot.completedInterviewCount)
        assertTrue(loaded.snapshot.isHistoryComplete)
        assertTrue(loaded.snapshot.canOpenMyInterviews)
    }

    @Test
    fun loadProfileDoesNotEnableActionForZeroOrIncompleteHistory() = runTest(dispatcher) {
        val zeroRemote = FakeProfileRemoteDataSource(
            historyPages = mutableMapOf(
                0 to RemoteResult.Success(InterviewHistoryPage(0, hasMore = false, nextPage = null)),
            )
        )
        val unavailableRemote = FakeProfileRemoteDataSource(
            historyPages = mutableMapOf(
                0 to RemoteResult.Failed(ProfileFailure.Offline),
            )
        )

        val zero = repository(zeroRemote).loadProfile() as ProfileLoadResult.Loaded
        val unavailable = repository(unavailableRemote).loadProfile()

        assertFalse(zero.snapshot.canOpenMyInterviews)
        val historyUnavailable = unavailable as ProfileLoadResult.HistoryUnavailable
        assertEquals("user@example.com", historyUnavailable.email)
        assertSame(ProfileFailure.Offline, historyUnavailable.reason)
    }

    @Test
    fun loadProfileReturnsInvalidSessionWithoutLeakingProfileData() = runTest(dispatcher) {
        val remote = FakeProfileRemoteDataSource(
            profileResult = RemoteResult.InvalidSession,
        )
        val repository = repository(remote)

        val result = repository.loadProfile()

        assertSame(ProfileLoadResult.InvalidSession, result)
        assertTrue(remote.requestedHistoryPages.isEmpty())
    }

    @Test
    fun loadProfilePropagatesCancellation() = runTest(dispatcher) {
        val historyGate = CompletableDeferred<Unit>()
        val remote = FakeProfileRemoteDataSource(
            historyPages = mutableMapOf(
                0 to RemoteResult.Success(InterviewHistoryPage(1, hasMore = false, nextPage = null)),
            ),
            historyGate = historyGate,
        )
        val repository = repository(remote)
        val job = async { repository.loadProfile() }

        dispatcher.scheduler.runCurrent()
        job.cancelAndJoin()

        assertTrue(job.isCancelled)
        assertEquals(listOf(0), remote.requestedHistoryPages)
    }

    @Test
    fun logoutBlocksRepeatedSubmissionUntilFirstRequestFinishes() = runTest(dispatcher) {
        val logoutGate = CompletableDeferred<Unit>()
        val remote = FakeProfileRemoteDataSource(logoutGate = logoutGate)
        val repository = repository(remote)

        val first = async { repository.logout() }
        dispatcher.scheduler.runCurrent()
        val second = repository.logout()
        logoutGate.complete(Unit)

        assertSame(LogoutResult.InProgress, second)
        assertSame(LogoutResult.Success, first.await())
        assertEquals(1, remote.logoutCalls)
    }

    @Test
    fun logoutKeepsFailureRecoverable() = runTest(dispatcher) {
        val remote = FakeProfileRemoteDataSource(
            logoutResult = RemoteResult.Failed(ProfileFailure.Offline),
        )
        val repository = repository(remote)

        val result = repository.logout()

        assertEquals(LogoutResult.Failed(ProfileFailure.Offline), result)
    }

    private fun repository(remote: FakeProfileRemoteDataSource): DefaultProfileRepository =
        DefaultProfileRepository(
            sessionTokenProvider = { "session-token" },
            remoteDataSource = remote,
            ioDispatcher = dispatcher,
        )
}

private class FakeProfileRemoteDataSource(
    private val profileResult: RemoteResult<ProfileIdentity> =
        RemoteResult.Success(ProfileIdentity("user@example.com")),
    val historyPages: MutableMap<Int, RemoteResult<InterviewHistoryPage>> = mutableMapOf(),
    private val logoutResult: RemoteResult<Unit> = RemoteResult.Success(Unit),
    private val historyGate: CompletableDeferred<Unit>? = null,
    private val logoutGate: CompletableDeferred<Unit>? = null,
) : ProfileRemoteDataSource {
    val requestedHistoryPages = mutableListOf<Int>()
    var logoutCalls = 0
        private set

    override suspend fun currentProfile(sessionToken: String): RemoteResult<ProfileIdentity> =
        profileResult

    override suspend fun interviewHistoryPage(
        sessionToken: String,
        page: Int,
    ): RemoteResult<InterviewHistoryPage> {
        requestedHistoryPages += page
        historyGate?.await()
        return historyPages.getValue(page)
    }

    override suspend fun logout(sessionToken: String): RemoteResult<Unit> {
        logoutCalls += 1
        logoutGate?.await()
        return logoutResult
    }
}
