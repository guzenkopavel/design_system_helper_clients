//
//  AuthResult.kt
//  SysDevSc
//
//  Created by Pavel Guzenko on 16.07.2026.
//  Copyright © 2026 Eltex. All rights reserved.
//

package ru.home.sysdevsc.auth.model

/**
 * Замкнутый тип результата операции авторизации.
 * Покрывает все наблюдаемые исходы: успех с сессионным секретом и почтой,
 * ошибка с сообщением, ограничение попыток и отсутствие сетевого подключения.
 */
sealed interface AuthResult {
    data class EmailChecked(val email: String, val exists: Boolean) : AuthResult
    data class Success(val token: String, val email: String) : AuthResult
    data class Failure(val message: String) : AuthResult
    data object RateLimited : AuthResult
    data object Offline : AuthResult
}
