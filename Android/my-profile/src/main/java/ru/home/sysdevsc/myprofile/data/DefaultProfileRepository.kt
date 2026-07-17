package ru.home.sysdevsc.myprofile.data

import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.withContext
import ru.home.sysdevsc.myprofile.model.InterviewHistoryPage
import ru.home.sysdevsc.myprofile.model.LogoutResult
import ru.home.sysdevsc.myprofile.model.ProfileFailure
import ru.home.sysdevsc.myprofile.model.ProfileLoadResult
import ru.home.sysdevsc.myprofile.model.ProfileSnapshot

class DefaultProfileRepository(
    private val sessionTokenProvider: suspend () -> String?,
    private val remoteDataSource: ProfileRemoteDataSource,
    private val ioDispatcher: CoroutineDispatcher = Dispatchers.IO,
) : ProfileRepository {

    private val logoutMutex = Mutex()

    override suspend fun loadProfile(): ProfileLoadResult {
        val sessionToken = sessionTokenProvider() ?: return ProfileLoadResult.InvalidSession
        return withContext(ioDispatcher) {
            when (val profile = remoteDataSource.currentProfile(sessionToken)) {
                is RemoteResult.Success -> loadHistory(sessionToken, profile.value.email)
                RemoteResult.InvalidSession -> ProfileLoadResult.InvalidSession
                is RemoteResult.Failed -> ProfileLoadResult.Failed(profile.reason)
            }
        }
    }

    override suspend fun logout(): LogoutResult {
        val sessionToken = sessionTokenProvider() ?: return LogoutResult.InvalidSession
        if (!logoutMutex.tryLock()) return LogoutResult.InProgress
        return try {
            withContext(ioDispatcher) {
                when (val result = remoteDataSource.logout(sessionToken)) {
                    is RemoteResult.Success -> LogoutResult.Success
                    RemoteResult.InvalidSession -> LogoutResult.InvalidSession
                    is RemoteResult.Failed -> LogoutResult.Failed(result.reason)
                }
            }
        } finally {
            logoutMutex.unlock()
        }
    }

    private suspend fun loadHistory(
        sessionToken: String,
        email: String,
    ): ProfileLoadResult {
        var nextPage = FIRST_HISTORY_PAGE
        var completedCount = 0

        while (true) {
            currentCoroutineContext().ensureActive()
            when (val page = remoteDataSource.interviewHistoryPage(sessionToken, nextPage)) {
                is RemoteResult.Success -> {
                    completedCount += page.value.completedInterviewCount
                    if (!page.value.hasMore) {
                        return ProfileLoadResult.Loaded(
                            ProfileSnapshot(
                                email = email,
                                completedInterviewCount = completedCount,
                                isHistoryComplete = true,
                            )
                        )
                    }
                    nextPage = page.value.nextPage ?: nextPage + 1
                }
                RemoteResult.InvalidSession -> return ProfileLoadResult.InvalidSession
                is RemoteResult.Failed -> return ProfileLoadResult.HistoryUnavailable(
                    email = email,
                    reason = page.reason,
                )
            }
        }
    }

    private companion object {
        const val FIRST_HISTORY_PAGE = 0
    }
}
