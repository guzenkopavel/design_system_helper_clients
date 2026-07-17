package ru.home.sysdevsc.myprofile.data

import kotlinx.coroutines.test.runTest
import okhttp3.OkHttpClient
import org.junit.Test
import kotlin.coroutines.cancellation.CancellationException

class DefaultProfileRemoteDataSourceTest {
    @Test(expected = CancellationException::class)
    fun currentProfilePropagatesCancellationFromHttpBoundary() = runTest {
        val client = OkHttpClient.Builder()
            .addInterceptor {
                throw CancellationException("cancelled")
            }
            .build()
        val source = DefaultProfileRemoteDataSource(
            baseUrl = "https://example.test",
            httpClient = client,
        )

        source.currentProfile("SessionCookie=test")
    }
}
