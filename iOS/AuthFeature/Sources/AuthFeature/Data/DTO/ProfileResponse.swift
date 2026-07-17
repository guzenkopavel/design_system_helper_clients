//
//  ProfileResponse.swift
//  AuthFeature
//
//  Created by Pavel Guzenko on 16.07.2025.
//  Copyright © 2025 Eltex. All rights reserved.
//

import Foundation

/// Ответ персонального запроса (проверка валидности сессии).
internal struct ProfileResponse: Decodable {

    let email: String
}
