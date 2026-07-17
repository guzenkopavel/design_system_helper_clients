package ru.home.sysdevsc.myprofile.data

import ru.home.sysdevsc.myprofile.model.LogoutResult
import ru.home.sysdevsc.myprofile.model.ProfileLoadResult

interface ProfileRepository {
    suspend fun loadProfile(): ProfileLoadResult
    suspend fun logout(): LogoutResult
}
