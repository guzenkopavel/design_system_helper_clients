package ru.home.sysdevsc

import android.content.Context
import android.security.NetworkSecurityPolicy
import androidx.activity.compose.setContent
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.hasSetTextAction
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onFirst
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTextInput
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import ru.home.sysdevsc.appshell.AppShell
import ru.home.sysdevsc.appshell.AppShellState
import ru.home.sysdevsc.auth.AuthGate
import ru.home.sysdevsc.auth.data.AuthApiService
import ru.home.sysdevsc.auth.data.EncryptedSessionRepository
import ru.home.sysdevsc.auth.data.SessionRepository
import ru.home.sysdevsc.auth.model.AuthResult
import ru.home.sysdevsc.ui.theme.SysDevScTheme
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicReference
import kotlin.coroutines.Continuation
import kotlin.coroutines.EmptyCoroutineContext
import kotlin.coroutines.startCoroutine

class AuthIntegrationTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun noSessionStartsAtEmailStepWithRealPlatformContext() {
        val repository = FakeSessionRepository()
        val api = FakeAuthApiService()
        lateinit var compositionContext: Context

        setActivityContent {
            compositionContext = LocalContext.current
            AuthenticatedApplication(api, repository)
        }

        composeRule.onNode(hasSetTextAction()).assertIsDisplayed()
        composeRule.onNodeWithText("Электронная почта").assertIsDisplayed()
        composeRule.runOnIdle {
            assertSame(composeRule.activity.applicationContext, compositionContext.applicationContext)
            assertEquals("ru.home.sysdevsc", compositionContext.applicationContext.packageName)
        }
    }

    @Test
    fun emailCheckMovesToPasswordStep() {
        val api = FakeAuthApiService()
        setActivityContent {
            AuthenticatedApplication(api, FakeSessionRepository())
        }

        composeRule.onNode(hasSetTextAction()).performTextInput(TEST_EMAIL)
        composeRule.onNodeWithText("Далее").performClick()

        composeRule.waitUntil(timeoutMillis = UI_TIMEOUT_MILLIS) {
            api.checkedEmails == listOf(TEST_EMAIL)
        }
        composeRule.onNodeWithText("Вход").assertIsDisplayed()
        composeRule.onNodeWithText(TEST_EMAIL).assertIsDisplayed()
        composeRule.onNodeWithText("Пароль").assertIsDisplayed()
    }

    @Test
    fun successfulLoginOpensCasesAndPersistsSession() {
        val repository = FakeSessionRepository()
        val api = FakeAuthApiService()
        setActivityContent {
            AuthenticatedApplication(api, repository)
        }

        composeRule.onNode(hasSetTextAction()).performTextInput(TEST_EMAIL)
        composeRule.onNodeWithText("Далее").performClick()
        composeRule.waitUntil(timeoutMillis = UI_TIMEOUT_MILLIS) {
            api.checkedEmails == listOf(TEST_EMAIL)
        }
        composeRule.onNodeWithText("Вход").assertIsDisplayed()
        composeRule.onNode(hasSetTextAction()).performTextInput(TEST_CREDENTIAL)
        composeRule.onNodeWithText("Войти").performClick()

        composeRule.waitUntil(timeoutMillis = UI_TIMEOUT_MILLIS) {
            repository.currentToken == SESSION_VALUE
        }
        composeRule.onAllNodesWithText("Кейсы").onFirst().assertIsDisplayed()
        assertEquals(listOf(TEST_EMAIL to TEST_CREDENTIAL), api.loginAttempts)
    }

    @Test
    fun newEmailRegistrationOpensCasesAndPersistsSession() {
        val repository = FakeSessionRepository()
        val api = FakeAuthApiService(emailExists = false)
        setActivityContent {
            AuthenticatedApplication(api, repository)
        }

        composeRule.onNode(hasSetTextAction()).performTextInput(TEST_EMAIL)
        composeRule.onNodeWithText("Далее").performClick()
        composeRule.waitUntil(timeoutMillis = UI_TIMEOUT_MILLIS) {
            api.checkedEmails == listOf(TEST_EMAIL)
        }
        composeRule.onNodeWithText("Регистрация").assertIsDisplayed()
        composeRule.onNode(hasSetTextAction()).performTextInput(TEST_CREDENTIAL)
        composeRule.onNodeWithText("Войти").performClick()

        composeRule.waitUntil(timeoutMillis = UI_TIMEOUT_MILLIS) {
            repository.currentToken == SESSION_VALUE
        }
        composeRule.onAllNodesWithText("Кейсы").onFirst().assertIsDisplayed()
        assertEquals(emptyList<Pair<String, String>>(), api.loginAttempts)
        assertEquals(listOf(TEST_EMAIL to TEST_CREDENTIAL), api.registerAttempts)
    }

    @Test
    fun persistedSessionSurvivesRepositoryReconstructionAndActivityRecreation() {
        val applicationContext = composeRule.activity.applicationContext
        val writerRepository = EncryptedSessionRepository(applicationContext)
        runSuspend { writerRepository.clearSession() }

        try {
            runSuspend { writerRepository.saveSession(SESSION_VALUE) }
            composeRule.activityRule.scenario.recreate()

            composeRule.onAllNodesWithText("Кейсы").onFirst().assertIsDisplayed()
            val reconstructedRepository = EncryptedSessionRepository(applicationContext)
            assertEquals(SESSION_VALUE, runSuspend { reconstructedRepository.getSession() })
        } finally {
            val cleanupRepository = EncryptedSessionRepository(applicationContext)
            runSuspend { cleanupRepository.clearSession() }
        }
    }

    @Test
    fun repositoryReportedExpiryClearsBoundaryAndReturnsToEmailStep() {
        val repository = ExpiringSessionRepository(EXPIRED_SESSION_VALUE)

        setActivityContent {
            AuthenticatedApplication(FakeAuthApiService(), repository)
        }

        composeRule.onNodeWithText("Электронная почта").assertIsDisplayed()
        assertEquals(1, repository.clearCount)
        assertFalse(repository.hasStoredSession)
    }

    @Test
    fun applicationBoundaryRejectsCleartextTraffic() {
        val context = composeRule.activity.applicationContext

        assertEquals("ru.home.sysdevsc", context.packageName)
        assertFalse(NetworkSecurityPolicy.getInstance().isCleartextTrafficPermitted)
    }

    private fun setActivityContent(content: @Composable () -> Unit) {
        composeRule.runOnUiThread {
            composeRule.activity.setContent(content = content)
        }
        composeRule.waitForIdle()
    }

    private fun <T> runSuspend(block: suspend () -> T): T {
        val completion = CountDownLatch(1)
        val outcome = AtomicReference<Result<T>>()
        block.startCoroutine(
            object : Continuation<T> {
                override val context = EmptyCoroutineContext

                override fun resumeWith(result: Result<T>) {
                    outcome.set(result)
                    completion.countDown()
                }
            },
        )
        assertTrue("suspend operation timed out", completion.await(ASYNC_TIMEOUT_SECONDS, TimeUnit.SECONDS))
        return outcome.get().getOrThrow()
    }

    @Composable
    private fun AuthenticatedApplication(
        api: AuthApiService,
        repository: SessionRepository,
    ) {
        var isAuthenticated by remember { mutableStateOf(false) }
        var appShellState by remember { mutableStateOf(AppShellState.initial()) }

        SysDevScTheme(dynamicColor = false) {
            if (isAuthenticated) {
                AppShell(
                    state = appShellState,
                    onDestinationSelected = { appShellState = appShellState.select(it) },
                )
            } else {
                AuthGate(
                    onAuthenticated = { isAuthenticated = true },
                    authApiService = api,
                    sessionRepository = repository,
                )
            }
        }
    }

    private class FakeSessionRepository : SessionRepository {
        var currentToken: String? = null
            private set
        var readCount: Int = 0
            private set
        var clearCount: Int = 0
            private set

        override suspend fun saveSession(token: String) {
            currentToken = token
        }

        override suspend fun getSession(): String? {
            readCount += 1
            return currentToken
        }

        override suspend fun clearSession() {
            currentToken = null
            clearCount += 1
        }
    }

    private class ExpiringSessionRepository(
        expiredToken: String,
    ) : SessionRepository {
        private var storedToken: String? = expiredToken

        var clearCount: Int = 0
            private set
        val hasStoredSession: Boolean
            get() = storedToken != null

        override suspend fun saveSession(token: String) {
            storedToken = token
        }

        override suspend fun getSession(): String? {
            if (storedToken != null) {
                clearSession()
            }
            return null
        }

        override suspend fun clearSession() {
            storedToken = null
            clearCount += 1
        }
    }

    private class FakeAuthApiService(
        private val emailExists: Boolean = true,
    ) : AuthApiService {
        val checkedEmails = mutableListOf<String>()
        val loginAttempts = mutableListOf<Pair<String, String>>()
        val registerAttempts = mutableListOf<Pair<String, String>>()

        override suspend fun checkEmail(email: String): AuthResult {
            checkedEmails += email
            return if (emailExists) {
                AuthResult.Success(token = EMAIL_EXISTS_MARKER, email = email)
            } else {
                AuthResult.Failure("Почта не найдена")
            }
        }

        override suspend fun login(email: String, password: String): AuthResult {
            loginAttempts += email to password
            return AuthResult.Success(token = SESSION_VALUE, email = email)
        }

        override suspend fun register(email: String, password: String): AuthResult {
            registerAttempts += email to password
            return AuthResult.Success(token = SESSION_VALUE, email = email)
        }
    }

    private companion object {
        const val TEST_EMAIL = "person@example.com"
        const val TEST_CREDENTIAL = "correct-pass"
        const val SESSION_VALUE = "persisted-session"
        const val EXPIRED_SESSION_VALUE = "repository-owned-expired"
        const val EMAIL_EXISTS_MARKER = "email-exists"
        const val UI_TIMEOUT_MILLIS = 5_000L
        const val ASYNC_TIMEOUT_SECONDS = 5L
    }
}
