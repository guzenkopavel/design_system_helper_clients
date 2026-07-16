//
//  AuthGate.kt
//  SysDevSc
//
//  Created by Pavel Guzenko on 16.07.2026.
//  Copyright © 2026 Eltex. All rights reserved.
//

package ru.home.sysdevsc.auth

import androidx.compose.runtime.Composable

/**
 * Корневой компонент авторизации.
 * Показывает флоу входа при отсутствии валидной сессии.
 *
 * @param onAuthenticated обратный вызов при успешной проверке.
 */
@Composable
fun AuthGate(onAuthenticated: () -> Unit) {
    // TODO: реализовать в task-004
}
