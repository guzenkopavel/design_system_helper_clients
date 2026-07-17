package ru.home.sysdevsc.myprofile.data

import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import ru.home.sysdevsc.myprofile.model.InterviewHistoryPage
import ru.home.sysdevsc.myprofile.model.ProfileFailure
import ru.home.sysdevsc.myprofile.model.ProfileIdentity
import java.util.concurrent.TimeUnit
import kotlin.coroutines.cancellation.CancellationException

class DefaultProfileRemoteDataSource(
    baseUrl: String,
    private val httpClient: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(5, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.SECONDS)
        .writeTimeout(10, TimeUnit.SECONDS)
        .build(),
) : ProfileRemoteDataSource {
    private val normalizedBaseUrl = baseUrl.trim().trimEnd('/')

    override suspend fun currentProfile(sessionToken: String): RemoteResult<ProfileIdentity> {
        val request = Request.Builder()
            .url("$normalizedBaseUrl/api/profile")
            .header("Cookie", sessionToken)
            .get()
            .build()

        return execute(request) { body ->
            val json = JSONObject(body.orEmpty())
            val profile = json.optJSONObject("profile") ?: json
            ProfileIdentity(email = profile.optString("email", ""))
        }
    }

    override suspend fun interviewHistoryPage(
        sessionToken: String,
        page: Int,
    ): RemoteResult<InterviewHistoryPage> {
        val request = Request.Builder()
            .url("$normalizedBaseUrl/api/interviews/history?page=$page")
            .header("Cookie", sessionToken)
            .get()
            .build()

        return execute(request) { body ->
            val json = JSONObject(body.orEmpty())
            val pageJson = json.optJSONObject("page")
            val items = json.optJSONArray("items")
                ?: json.optJSONArray("interviews")
            InterviewHistoryPage(
                completedInterviewCount = items?.length() ?: json.optInt("count", 0),
                hasMore = pageJson?.optBoolean("hasMore")
                    ?: json.optBoolean("hasMore", false),
                nextPage = pageJson?.takeIf { it.has("nextPage") }?.optInt("nextPage")
                    ?: json.takeIf { it.has("nextPage") }?.optInt("nextPage"),
            )
        }
    }

    override suspend fun logout(sessionToken: String): RemoteResult<Unit> {
        val request = Request.Builder()
            .url("$normalizedBaseUrl/api/auth/logout")
            .header("Cookie", sessionToken)
            .post(ByteArray(0).toRequestBody(null))
            .build()

        return execute(request) { Unit }
    }

    private fun <T> execute(
        request: Request,
        parse: (String?) -> T,
    ): RemoteResult<T> {
        return try {
            httpClient.newCall(request).execute().use { response ->
                val body = response.body?.string()
                when (response.code) {
                    200, 204 -> RemoteResult.Success(parse(body))
                    401, 403 -> RemoteResult.InvalidSession
                    else -> RemoteResult.Failed(
                        ProfileFailure.Server(parseServerMessage(body, "Ошибка сервера: ${response.code}"))
                    )
                }
            }
        } catch (cancellation: CancellationException) {
            throw cancellation
        } catch (_: Exception) {
            RemoteResult.Failed(ProfileFailure.Offline)
        }
    }

    private fun parseServerMessage(body: String?, fallback: String): String {
        if (body.isNullOrBlank()) return fallback
        return runCatching {
            JSONObject(body)
                .optJSONObject("error")
                ?.optString("message")
                ?.takeIf { it.isNotBlank() }
                ?: fallback
        }.getOrDefault(fallback)
    }
}
