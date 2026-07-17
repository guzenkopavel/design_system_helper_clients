//
//  DefaultAuthApiService.kt
//  SysDevSc
//
//  Created by Pavel Guzenko on 16.07.2026.
//  Copyright © 2026 Eltex. All rights reserved.
//

package ru.home.sysdevsc.auth.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.Call
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import ru.home.sysdevsc.auth.model.AuthResult

/**
 * Реализация сетевого контракта авторизации на базе OkHttp.
 * Выполняет запросы проверки почты, входа и регистрации
 * по адресу API, задаваемому как внешний параметр.
 * Все запросы строго по HTTPS — cleartext запрещён
 * конфигурацией сетевой безопасности приложения.
 */
class DefaultAuthApiService(
    private val baseUrl: String,
    private val httpClient: OkHttpClient = OkHttpClient.Builder().build()
) : AuthApiService {

    private val jsonMediaType = "application/json; charset=utf-8".toMediaTypeOrNull()

    override suspend fun checkEmail(email: String): AuthResult = withContext(Dispatchers.IO) {
        val url = "$baseUrl/auth/check-email"
        val body = JSONObject().apply { put("email", email) }.toString().toRequestBody(jsonMediaType)

        val request = Request.Builder()
            .url(url)
            .post(body)
            .build()

        executeAuthRequest(request)
    }

    override suspend fun login(email: String, password: String): AuthResult = withContext(Dispatchers.IO) {
        val url = "$baseUrl/auth/login"
        val body = JSONObject().apply {
            put("email", email)
            put("password", password)
        }.toString().toRequestBody(jsonMediaType)

        val request = Request.Builder()
            .url(url)
            .post(body)
            .build()

        executeAuthRequest(request)
    }

    override suspend fun register(email: String, password: String): AuthResult = withContext(Dispatchers.IO) {
        val url = "$baseUrl/auth/register"
        val body = JSONObject().apply {
            put("email", email)
            put("password", password)
        }.toString().toRequestBody(jsonMediaType)

        val request = Request.Builder()
            .url(url)
            .post(body)
            .build()

        executeAuthRequest(request)
    }

    private fun executeAuthRequest(request: Request): AuthResult {
        val call: Call = httpClient.newCall(request)
        return try {
            val response = call.execute()
            when (response.code) {
                200 -> {
                    val responseBody = response.body?.string()
                    if (!responseBody.isNullOrEmpty()) {
                        val json = JSONObject(responseBody)
                        val token = json.optString("token", "")
                        val email = json.optString("email", "")
                        if (token.isNotEmpty()) {
                            AuthResult.Success(token = token, email = email)
                        } else {
                            AuthResult.Failure("Пустой токен в ответе сервера")
                        }
                    } else {
                        AuthResult.Failure("Пустой ответ сервера")
                    }
                }
                401 -> AuthResult.Failure("Неверные учётные данные")
                409 -> AuthResult.Failure("Аккаунт с такой почтой уже существует")
                422 -> AuthResult.Failure("Почта не найдена, создайте аккаунт")
                429 -> AuthResult.RateLimited
                else -> AuthResult.Failure("Ошибка сервера: ${response.code}")
            }
        } catch (e: Exception) {
            if (e.message?.contains("etag", ignoreCase = true) == true ||
                e.message?.contains("unreachable", ignoreCase = true) == true ||
                e.message?.contains("failed to connect", ignoreCase = true) == true) {
                AuthResult.Offline
            } else {
                AuthResult.Offline
            }
        }
    }
}
