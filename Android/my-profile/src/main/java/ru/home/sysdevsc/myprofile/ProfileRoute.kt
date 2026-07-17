package ru.home.sysdevsc.myprofile

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import kotlinx.coroutines.launch
import ru.home.sysdevsc.myprofile.data.ProfileRepository
import ru.home.sysdevsc.myprofile.model.LogoutResult
import ru.home.sysdevsc.myprofile.model.ProfileFailure
import ru.home.sysdevsc.myprofile.model.ProfileLoadResult
import ru.home.sysdevsc.myprofile.ui.ProfileScreen
import ru.home.sysdevsc.myprofile.ui.ProfileUiState

@Composable
fun ProfileRoute(
    repository: ProfileRepository,
    onSessionEnded: suspend () -> Unit,
    modifier: Modifier = Modifier,
) {
    val coroutineScope = rememberCoroutineScope()
    val offlineMessage = stringResource(R.string.my_profile_history_unknown)
    var state by remember {
        mutableStateOf(
            ProfileUiState(
                email = null,
                completedInterviewCount = null,
                isHistoryComplete = false,
                isHistoryLoading = true,
                recoveryMessage = null,
                isLogoutInProgress = false,
            )
        )
    }

    fun failureMessage(reason: ProfileFailure): String =
        when (reason) {
            ProfileFailure.Offline -> offlineMessage
            is ProfileFailure.Server -> reason.message
        }

    LaunchedEffect(repository) {
        state = state.copy(isHistoryLoading = true, recoveryMessage = null)
        when (val result = repository.loadProfile()) {
            is ProfileLoadResult.Loaded -> {
                state = ProfileUiState(
                    email = result.snapshot.email,
                    completedInterviewCount = result.snapshot.completedInterviewCount,
                    isHistoryComplete = result.snapshot.isHistoryComplete,
                    isHistoryLoading = false,
                    recoveryMessage = null,
                    isLogoutInProgress = false,
                )
            }
            is ProfileLoadResult.HistoryUnavailable -> {
                state = ProfileUiState(
                    email = result.email,
                    completedInterviewCount = null,
                    isHistoryComplete = false,
                    isHistoryLoading = false,
                    recoveryMessage = failureMessage(result.reason),
                    isLogoutInProgress = false,
                )
            }
            is ProfileLoadResult.Failed -> {
                state = state.copy(
                    isHistoryLoading = false,
                    recoveryMessage = failureMessage(result.reason),
                )
            }
            ProfileLoadResult.InvalidSession -> onSessionEnded()
        }
    }

    ProfileScreen(
        state = state,
        onMyInterviewsClick = {},
        onLogoutClick = {
            if (!state.isLogoutInProgress) {
                state = state.copy(isLogoutInProgress = true, recoveryMessage = null)
                coroutineScope.launch {
                    when (val result = repository.logout()) {
                        LogoutResult.Success,
                        LogoutResult.InvalidSession -> onSessionEnded()
                        LogoutResult.InProgress -> {
                            state = state.copy(isLogoutInProgress = true)
                        }
                        is LogoutResult.Failed -> {
                            state = state.copy(
                                isLogoutInProgress = false,
                                recoveryMessage = failureMessage(result.reason),
                            )
                        }
                    }
                }
            }
        },
        modifier = modifier,
    )
}
