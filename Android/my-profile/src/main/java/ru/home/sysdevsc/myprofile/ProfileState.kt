package ru.home.sysdevsc.myprofile

sealed interface ProfileState {
    data object Loading : ProfileState

    data class Ready(
        val email: String,
        val completedInterviewCount: Int,
        val isHistoryComplete: Boolean,
        val isLogoutInProgress: Boolean = false,
    ) : ProfileState {
        val canOpenMyInterviews: Boolean
            get() = isHistoryComplete && completedInterviewCount > 0
    }

    data class Recovery(
        val email: String?,
        val message: String,
        val isLogoutAvailable: Boolean,
    ) : ProfileState

    data object InvalidSession : ProfileState
}
