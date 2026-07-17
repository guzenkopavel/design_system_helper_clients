package ru.home.sysdevsc

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.tooling.preview.Preview
import ru.home.sysdevsc.appshell.AppShell
import ru.home.sysdevsc.appshell.AppShellState
import ru.home.sysdevsc.auth.AuthGate
import ru.home.sysdevsc.auth.data.EncryptedSessionRepository
import ru.home.sysdevsc.myprofile.ProfileRoute
import ru.home.sysdevsc.myprofile.data.DefaultProfileRemoteDataSource
import ru.home.sysdevsc.myprofile.data.DefaultProfileRepository
import ru.home.sysdevsc.ui.theme.SysDevScTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            SysDevScApp()
        }
    }
}

@Composable
fun SysDevScApp(modifier: Modifier = Modifier) {
    var appShellState by remember { mutableStateOf(AppShellState.initial()) }
    var isAuthenticated by remember { mutableStateOf(false) }
    val context = LocalContext.current
    val sessionRepository = remember(context) { EncryptedSessionRepository(context) }

    SysDevScTheme {
        if (isAuthenticated) {
            AppShell(
                state = appShellState,
                onDestinationSelected = { destination ->
                    appShellState = appShellState.select(destination)
                },
                modifier = modifier,
                profileContent = {
                    ProfileDestinationContent(
                        sessionRepository = sessionRepository,
                        onSessionEnded = {
                            appShellState = AppShellState.initial()
                            isAuthenticated = false
                        },
                    )
                },
            )
        } else {
            AuthGate(
                onAuthenticated = { isAuthenticated = true },
                modifier = modifier
            )
        }
    }
}

@Composable
private fun ProfileDestinationContent(
    sessionRepository: EncryptedSessionRepository,
    onSessionEnded: () -> Unit,
) {
    val context = LocalContext.current
    val repository = remember(context, sessionRepository) {
        DefaultProfileRepository(
            sessionTokenProvider = sessionRepository::getSession,
            remoteDataSource = DefaultProfileRemoteDataSource(
                baseUrl = context.getString(R.string.auth_api_base_url),
            ),
        )
    }

    ProfileRoute(
        repository = repository,
        onSessionEnded = {
            sessionRepository.clearSession()
            onSessionEnded()
        },
    )
}

@Preview(showBackground = true)
@Composable
fun SysDevScAppPreview() {
    SysDevScApp()
}
