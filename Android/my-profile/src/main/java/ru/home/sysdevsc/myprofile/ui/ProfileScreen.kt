package ru.home.sysdevsc.myprofile.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.disabled
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import ru.home.sysdevsc.myprofile.R

@Immutable
data class ProfileUiState(
    val email: String?,
    val completedInterviewCount: Int?,
    val isHistoryComplete: Boolean,
    val isHistoryLoading: Boolean,
    val recoveryMessage: String?,
    val isLogoutInProgress: Boolean,
) {
    val canOpenMyInterviews: Boolean
        get() = isHistoryComplete && (completedInterviewCount ?: 0) > 0
}

@Composable
fun ProfileScreen(
    state: ProfileUiState,
    onMyInterviewsClick: () -> Unit,
    onLogoutClick: () -> Unit,
    modifier: Modifier = Modifier,
    snackbarHostState: SnackbarHostState = remember { SnackbarHostState() },
) {
    val coroutineScope = rememberCoroutineScope()
    val countFeedback = state.completedInterviewCount?.let {
        stringResource(R.string.my_profile_interviews_count, it)
    }

    Scaffold(
        modifier = modifier.fillMaxSize(),
        snackbarHost = { SnackbarHost(hostState = snackbarHostState) },
        containerColor = MaterialTheme.colorScheme.surface,
        contentColor = MaterialTheme.colorScheme.onSurface,
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(horizontal = 24.dp, vertical = 28.dp),
            contentAlignment = Alignment.TopCenter,
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .testTag("my_profile_content"),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(18.dp),
            ) {
                AccountMarker()
                EmailBlock(email = state.email)
                HistoryStateMessage(state = state)
                ProfileActions(
                    state = state,
                    countFeedback = countFeedback,
                    onMyInterviewsClick = onMyInterviewsClick,
                    onLogoutClick = onLogoutClick,
                    onShowFeedback = { message ->
                        coroutineScope.launch {
                            snackbarHostState.showSnackbar(message)
                        }
                    },
                )
            }
        }
    }
}

@Composable
private fun AccountMarker() {
    val markerDescription = stringResource(R.string.my_profile_account_marker)
    Surface(
        modifier = Modifier
            .size(92.dp)
            .clip(CircleShape)
            .semantics { contentDescription = markerDescription },
        shape = CircleShape,
        color = MaterialTheme.colorScheme.primaryContainer,
        contentColor = MaterialTheme.colorScheme.onPrimaryContainer,
    ) {
        Box(contentAlignment = Alignment.Center) {
            Text(
                text = stringResource(R.string.my_profile_account_marker_symbol),
                style = MaterialTheme.typography.displaySmall,
                textAlign = TextAlign.Center,
            )
        }
    }
}

@Composable
private fun EmailBlock(email: String?) {
    val emailLabel = stringResource(R.string.my_profile_email_semantics)
    val emailText = email ?: stringResource(R.string.my_profile_email_loading)
    Text(
        text = emailText,
        modifier = Modifier
            .fillMaxWidth()
            .semantics { contentDescription = "$emailLabel: $emailText" },
        style = MaterialTheme.typography.titleMedium,
        color = MaterialTheme.colorScheme.onSurface,
        textAlign = TextAlign.Center,
        maxLines = 2,
        overflow = TextOverflow.Ellipsis,
    )
}

@Composable
private fun HistoryStateMessage(state: ProfileUiState) {
    val message = when {
        state.isHistoryLoading -> stringResource(R.string.my_profile_history_loading)
        state.recoveryMessage != null -> state.recoveryMessage
        !state.isHistoryComplete -> stringResource(R.string.my_profile_history_unknown)
        state.completedInterviewCount == 0 -> stringResource(R.string.my_profile_history_empty)
        else -> null
    }
    if (message != null) {
        Text(
            text = message,
            modifier = Modifier
                .fillMaxWidth()
                .testTag("my_profile_history_state"),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
        )
    } else {
        Spacer(modifier = Modifier.height(4.dp))
    }
}

@Composable
private fun ProfileActions(
    state: ProfileUiState,
    countFeedback: String?,
    onMyInterviewsClick: () -> Unit,
    onLogoutClick: () -> Unit,
    onShowFeedback: (String) -> Unit,
) {
    val disabledDescription = stringResource(R.string.my_profile_my_interviews_disabled_semantics)
    val logoutBusy = stringResource(R.string.my_profile_logout_busy_semantics)

    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
        Button(
            onClick = {
                if (countFeedback != null) {
                    onShowFeedback(countFeedback)
                }
                onMyInterviewsClick()
            },
            enabled = state.canOpenMyInterviews,
            modifier = Modifier
                .fillMaxWidth()
                .testTag("my_profile_my_interviews")
                .semantics {
                    role = Role.Button
                    if (!state.canOpenMyInterviews) {
                        disabled()
                        stateDescription = disabledDescription
                    }
                },
            colors = ButtonDefaults.buttonColors(
                containerColor = MaterialTheme.colorScheme.primary,
                contentColor = MaterialTheme.colorScheme.onPrimary,
                disabledContainerColor = MaterialTheme.colorScheme.surfaceVariant,
                disabledContentColor = MaterialTheme.colorScheme.onSurfaceVariant,
            ),
        ) {
            Text(text = stringResource(R.string.my_profile_my_interviews))
        }
        OutlinedButton(
            onClick = onLogoutClick,
            enabled = !state.isLogoutInProgress,
            modifier = Modifier
                .fillMaxWidth()
                .testTag("my_profile_logout")
                .semantics {
                    role = Role.Button
                    if (state.isLogoutInProgress) {
                        stateDescription = logoutBusy
                    }
                },
            colors = ButtonDefaults.outlinedButtonColors(
                contentColor = MaterialTheme.colorScheme.error,
                disabledContentColor = MaterialTheme.colorScheme.onSurfaceVariant,
            ),
        ) {
            Row(
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                if (state.isLogoutInProgress) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(18.dp),
                        strokeWidth = 2.dp,
                    )
                }
                Text(text = stringResource(R.string.my_profile_logout))
            }
        }
    }
}
