//
//  EncryptedSessionRepository.kt
//  SysDevSc
//
//  Created by Pavel Guzenko on 16.07.2026.
//  Copyright © 2026 Eltex. All rights reserved.
//

package ru.home.sysdevsc.auth.data

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

/**
 * Реализация SessionRepository на базе EncryptedSharedPreferences.
 * Хранит сессионный токен в зашифрованном хранилище, недоступном
 * другим приложениям. Пароль не сохраняется — только токен.
 *
 * @param context Android Context для доступа к shared preferences.
 */
class EncryptedSessionRepository(context: Context) : SessionRepository {

    private val prefs: SharedPreferences = run {
        val masterKeyAlias = "master_key_alias"
        val masterKey = MasterKey.Builder(context, masterKeyAlias)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        EncryptedSharedPreferences.create(
            context,
            "auth_session_prefs",
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }

    private companion object {
        private const val KEY_TOKEN = "session_token"
    }

    override suspend fun saveSession(token: String) {
        prefs.edit()
            .putString(KEY_TOKEN, token)
            .apply()
    }

    override suspend fun getSession(): String? {
        return prefs.getString(KEY_TOKEN, null)
    }

    override suspend fun clearSession() {
        prefs.edit()
            .remove(KEY_TOKEN)
            .apply()
    }
}
