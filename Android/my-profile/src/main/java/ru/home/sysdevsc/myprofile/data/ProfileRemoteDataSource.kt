package ru.home.sysdevsc.myprofile.data

import ru.home.sysdevsc.myprofile.model.InterviewHistoryPage
import ru.home.sysdevsc.myprofile.model.ProfileFailure
import ru.home.sysdevsc.myprofile.model.ProfileIdentity

interface ProfileRemoteDataSource {
    suspend fun currentProfile(sessionToken: String): RemoteResult<ProfileIdentity>
    suspend fun interviewHistoryPage(sessionToken: String, page: Int): RemoteResult<InterviewHistoryPage>
    suspend fun logout(sessionToken: String): RemoteResult<Unit>
}

sealed interface RemoteResult<out T> {
    data class Success<T>(val value: T) : RemoteResult<T>
    data object InvalidSession : RemoteResult<Nothing>
    data class Failed(val reason: ProfileFailure) : RemoteResult<Nothing>
}
