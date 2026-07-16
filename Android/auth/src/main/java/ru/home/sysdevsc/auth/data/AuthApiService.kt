//
//  AuthApiService.kt
//  SysDevSc
//
//  Created by Pavel Guzenko on 16.07.2026.
//  Copyright © 2026 Eltex. All rights reserved.
//

package ru.home.sysdevsc.auth.data

import ru.home.sysdevsc.auth.model.AuthResult

/**
 * Сетевой контракт сервиса авторизации.
 * Предоставляет асинхронные операции проверки адреса почты,
 * входа и регистрации. Реализация отвечает за TLS,
 * заголовки и сериализацию — интерфейс не зависит от
 * конкретного HTTP-клиента.
 */
interface AuthApiService {
    /**
     * Проверяет, зарегистрирован ли адрес электронной почты.
     * Ответ определяет ветвление: вход или регистрация.
     */
    suspend fun checkEmail(email: String): AuthResult

    /**
     * Выполняет вход по существующему аккаунту.
     */
    suspend fun login(email: String, password: String): AuthResult

    /**
     * Регистрирует новую пару почта/пароль.
     */
    suspend fun register(email: String, password: String): AuthResult
}
