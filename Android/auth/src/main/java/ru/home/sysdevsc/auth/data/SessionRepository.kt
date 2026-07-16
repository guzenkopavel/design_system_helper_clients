//
//  SessionRepository.kt
//  SysDevSc
//
//  Created by Pavel Guzenko on 16.07.2026.
//  Copyright © 2026 Eltex. All rights reserved.
//

package ru.home.sysdevsc.auth.data

/**
 * Публичная граница хранилища сессионного секрета.
 * Реализация использует защищённое хранилище платформы
 * (AndroidX Security Crypto), недоступное другим приложениям.
 * Пароль не сохраняется — только сессионный токен.
 */
interface SessionRepository {
    suspend fun saveSession(token: String)
    suspend fun getSession(): String?
    suspend fun clearSession()
}
