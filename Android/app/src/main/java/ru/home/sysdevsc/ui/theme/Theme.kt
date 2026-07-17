package ru.home.sysdevsc.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val DarkColorScheme = darkColorScheme(
    primary = SoftBlueDarkPrimary,
    onPrimary = SoftBlueDarkOnPrimary,
    secondaryContainer = SoftBlueDarkSecondaryContainer,
    onSecondaryContainer = SoftBlueDarkOnSecondaryContainer,
    surface = SoftBlueDarkSurface,
    onSurface = SoftBlueDarkOnSurface
)

private val LightColorScheme = lightColorScheme(
    primary = SoftBlueLightPrimary,
    onPrimary = SoftBlueLightOnPrimary,
    secondaryContainer = SoftBlueLightSecondaryContainer,
    onSecondaryContainer = SoftBlueLightOnSecondaryContainer,
    surface = SoftBlueLightSurface,
    onSurface = SoftBlueLightOnSurface
)

@Composable
fun SysDevScTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = false,
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
