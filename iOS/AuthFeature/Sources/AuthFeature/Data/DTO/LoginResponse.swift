//
//  LoginResponse.swift
//  AuthFeature
//
//  Created by Pavel Guzenko on 16.07.2025.
//  Copyright © 2025 Eltex. All rights reserved.
//

import Foundation

/// Ответ на вход (данные пользователя, cookie извлекается отдельно).
internal struct LoginResponse: Decodable {

    let user: User

    struct User: Decodable {
        let email: String
    }
}
