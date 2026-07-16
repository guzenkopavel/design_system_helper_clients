package ru.home.sysdevsc.appshell

import androidx.annotation.StringRes
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.colorResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.unit.dp

@Composable
fun AppShell(
    state: AppShellState,
    onDestinationSelected: (AppShellDestination) -> Unit,
    modifier: Modifier = Modifier,
    darkTheme: Boolean = false,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) appShellDarkColorScheme() else appShellLightColorScheme(),
    ) {
        Scaffold(
            modifier = modifier.fillMaxSize(),
            bottomBar = {
                AppShellNavigationBar(
                    state = state,
                    onDestinationSelected = onDestinationSelected,
                )
            }
        ) { innerPadding ->
            AppShellDestinationSurface(
                destination = state.selectedDestination,
                contentPadding = innerPadding,
            )
        }
    }
}

@Composable
private fun AppShellNavigationBar(
    state: AppShellState,
    onDestinationSelected: (AppShellDestination) -> Unit,
) {
    NavigationBar {
        val selectedState = stringResource(R.string.app_shell_semantics_selected)
        val notSelectedState = stringResource(R.string.app_shell_semantics_not_selected)

        AppShellDestination.entries.forEach { destination ->
            val label = stringResource(destination.labelResId())
            val selected = destination == state.selectedDestination

            NavigationBarItem(
                selected = selected,
                onClick = { onDestinationSelected(destination) },
                icon = {
                    Text(
                        text = if (selected) "●" else "○",
                        modifier = Modifier.semantics {
                            stateDescription = if (selected) selectedState else notSelectedState
                        }
                    )
                },
                label = { Text(text = label) },
                alwaysShowLabel = true,
                modifier = Modifier
                    .testTag(destination.testTag())
                    .semantics {
                        stateDescription = if (selected) selectedState else notSelectedState
                    },
            )
        }
    }
}

@Composable
private fun AppShellDestinationSurface(
    destination: AppShellDestination,
    contentPadding: PaddingValues,
) {
    Surface(
        modifier = Modifier
            .fillMaxSize()
            .padding(contentPadding)
            .testTag("app_shell_surface"),
        color = MaterialTheme.colorScheme.surface,
        contentColor = MaterialTheme.colorScheme.onSurface,
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
        ) {
            Text(
                text = stringResource(destination.labelResId()),
                style = MaterialTheme.typography.headlineSmall,
            )
            Text(
                text = stringResource(destination.surfaceTextResId()),
                modifier = Modifier.padding(top = 12.dp),
                style = MaterialTheme.typography.bodyLarge,
            )
        }
    }
}

@Composable
private fun appShellLightColorScheme() = lightColorScheme(
    primary = colorResource(R.color.app_shell_soft_blue_primary),
    onPrimary = colorResource(R.color.app_shell_soft_blue_on_primary),
    primaryContainer = colorResource(R.color.app_shell_soft_blue_primary_container),
    onPrimaryContainer = colorResource(R.color.app_shell_soft_blue_on_primary_container),
    surface = colorResource(R.color.app_shell_light_surface),
    onSurface = colorResource(R.color.app_shell_light_on_surface),
)

@Composable
private fun appShellDarkColorScheme() = darkColorScheme(
    primary = colorResource(R.color.app_shell_soft_blue_dark_primary),
    onPrimary = colorResource(R.color.app_shell_soft_blue_dark_on_primary),
    primaryContainer = colorResource(R.color.app_shell_soft_blue_dark_primary_container),
    onPrimaryContainer = colorResource(R.color.app_shell_soft_blue_dark_on_primary_container),
    surface = colorResource(R.color.app_shell_dark_surface),
    onSurface = colorResource(R.color.app_shell_dark_on_surface),
)

@StringRes
private fun AppShellDestination.labelResId(): Int =
    when (this) {
        AppShellDestination.Cases -> R.string.app_shell_destination_cases
        AppShellDestination.Knowledge -> R.string.app_shell_destination_knowledge
        AppShellDestination.Profile -> R.string.app_shell_destination_profile
    }

@StringRes
private fun AppShellDestination.surfaceTextResId(): Int =
    when (this) {
        AppShellDestination.Cases -> R.string.app_shell_surface_cases
        AppShellDestination.Knowledge -> R.string.app_shell_surface_knowledge
        AppShellDestination.Profile -> R.string.app_shell_surface_profile
    }

private fun AppShellDestination.testTag(): String =
    when (this) {
        AppShellDestination.Cases -> "app_shell_destination_cases"
        AppShellDestination.Knowledge -> "app_shell_destination_knowledge"
        AppShellDestination.Profile -> "app_shell_destination_profile"
    }
