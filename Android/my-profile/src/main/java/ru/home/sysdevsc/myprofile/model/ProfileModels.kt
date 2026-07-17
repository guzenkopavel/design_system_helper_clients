package ru.home.sysdevsc.myprofile.model

data class ProfileIdentity(
    val email: String,
)

data class InterviewHistoryPage(
    val completedInterviewCount: Int,
    val hasMore: Boolean,
    val nextPage: Int?,
)

data class ProfileSnapshot(
    val email: String,
    val completedInterviewCount: Int,
    val isHistoryComplete: Boolean,
) {
    val canOpenMyInterviews: Boolean
        get() = isHistoryComplete && completedInterviewCount > 0
}

sealed interface ProfileLoadResult {
    data class Loaded(val snapshot: ProfileSnapshot) : ProfileLoadResult
    data class HistoryUnavailable(
        val email: String,
        val reason: ProfileFailure,
    ) : ProfileLoadResult
    data object InvalidSession : ProfileLoadResult
    data class Failed(val reason: ProfileFailure) : ProfileLoadResult
}

sealed interface LogoutResult {
    data object Success : LogoutResult
    data object InvalidSession : LogoutResult
    data object InProgress : LogoutResult
    data class Failed(val reason: ProfileFailure) : LogoutResult
}

sealed interface ProfileFailure {
    data object Offline : ProfileFailure
    data class Server(val message: String) : ProfileFailure
}
