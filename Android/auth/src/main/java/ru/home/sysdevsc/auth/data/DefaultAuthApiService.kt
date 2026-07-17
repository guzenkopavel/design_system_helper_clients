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
import java.util.concurrent.TimeUnit

/**
 * Реализация сетевого контракта авторизации на базе OkHttp.
 * Выполняет запросы проверки почты, входа и регистрации
 * по адресу API, задаваемому как внешний параметр.
 * Все запросы строго по HTTPS — cleartext запрещён
 * конфигурацией сетевой безопасности приложения.
 */
class DefaultAuthApiService(
    private val baseUrl: String,
    private val httpClient: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(5, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.SECONDS)
        .writeTimeout(10, TimeUnit.SECONDS)
        .build()
) : AuthApiService {

    private val jsonMediaType = "application/json; charset=utf-8".toMediaTypeOrNull()
    private val normalizedBaseUrl = baseUrl.trim().trimEnd('/')

    override suspend fun checkEmail(email: String): AuthResult = withContext(Dispatchers.IO) {
        val url = "$normalizedBaseUrl/api/auth/email-check"
        val body = JSONObject().apply { put("email", email) }.toString().toRequestBody(jsonMediaType)

        val request = Request.Builder()
            .url(url)
            .post(body)
            .build()

        executeEmailCheckRequest(request, email)
    }

    override suspend fun login(email: String, password: String): AuthResult = withContext(Dispatchers.IO) {
        val url = "$normalizedBaseUrl/api/auth/login"
        val body = JSONObject().apply {
            put("email", email)
            put("password", password)
        }.toString().toRequestBody(jsonMediaType)

        val request = Request.Builder()
            .url(url)
            .post(body)
            .build()

        executeSessionRequest(request, successCodes = setOf(200))
    }

    override suspend fun register(email: String, password: String): AuthResult = withContext(Dispatchers.IO) {
        val url = "$normalizedBaseUrl/api/auth/register"
        val body = JSONObject().apply {
            put("email", email)
            put("password", password)
        }.toString().toRequestBody(jsonMediaType)

        val request = Request.Builder()
            .url(url)
            .post(body)
            .build()

        executeSessionRequest(request, successCodes = setOf(201))
    }

    private fun executeEmailCheckRequest(request: Request, requestedEmail: String): AuthResult {
        val call: Call = httpClient.newCall(request)
        return try {
            val response = call.execute()
            val responseBody = response.body?.string()
            when (response.code) {
                200 -> {
                    if (!responseBody.isNullOrEmpty()) {
                        val json = JSONObject(responseBody)
                        val email = json.optString("email", "")
                        AuthResult.EmailChecked(
                            email = email.ifEmpty { requestedEmail },
                            exists = json.optBoolean("exists", false)
                        )
                    } else {
                        AuthResult.Failure("Пустой ответ сервера")
                    }
                }
                422 -> AuthResult.Failure(parseServerMessage(responseBody, "Некорректный адрес электронной почты"))
                429 -> AuthResult.RateLimited
                else -> AuthResult.Failure(parseServerMessage(responseBody, "Ошибка сервера: ${response.code}"))
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

    private fun executeSessionRequest(request: Request, successCodes: Set<Int>): AuthResult {
        val call: Call = httpClient.newCall(request)
        return try {
            val response = call.execute()
            val responseBody = response.body?.string()
            when (response.code) {
                in successCodes -> {
                    val sessionCookie = extractSessionCookie(response.headers("Set-Cookie"))
                    if (sessionCookie.isNotEmpty()) {
                        val email = parseProfileEmail(responseBody)
                        AuthResult.Success(token = sessionCookie, email = email)
                    } else {
                        AuthResult.Failure("Сервер не вернул сессионную cookie")
                    }
                }
                401 -> AuthResult.Failure(parseServerMessage(responseBody, "Неверные учётные данные"))
                409 -> AuthResult.Failure(parseServerMessage(responseBody, "Аккаунт с такой почтой уже существует"))
                422 -> AuthResult.Failure(parseServerMessage(responseBody, "Некорректные данные"))
                429 -> AuthResult.RateLimited
                else -> AuthResult.Failure(parseServerMessage(responseBody, "Ошибка сервера: ${response.code}"))
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

    private fun extractSessionCookie(cookies: List<String>): String {
        return cookies
            .firstOrNull { it.startsWith("dsh_session=", ignoreCase = true) }
            ?.substringBefore(';')
            .orEmpty()
    }

    private fun parseProfileEmail(responseBody: String?): String {
        if (responseBody.isNullOrEmpty()) return ""
        return runCatching {
            JSONObject(responseBody)
                .optJSONObject("profile")
                ?.optString("email", "")
                .orEmpty()
        }.getOrDefault("")
    }

    private fun parseServerMessage(responseBody: String?, fallback: String): String {
        if (responseBody.isNullOrEmpty()) return fallback
        return runCatching {
            JSONObject(responseBody)
                .optJSONObject("error")
                ?.optString("message")
                ?.takeIf { it.isNotBlank() }
                ?: fallback
        }.getOrDefault(fallback)
    }
}
