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
import androidx.compose.ui.tooling.preview.Preview
import ru.home.sysdevsc.appshell.AppShell
import ru.home.sysdevsc.appshell.AppShellState
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

    SysDevScTheme {
        AppShell(
            state = appShellState,
            onDestinationSelected = { destination ->
                appShellState = appShellState.select(destination)
            },
            modifier = modifier,
        )
    }
}

@Preview(showBackground = true)
@Composable
fun SysDevScAppPreview() {
    SysDevScApp()
}
