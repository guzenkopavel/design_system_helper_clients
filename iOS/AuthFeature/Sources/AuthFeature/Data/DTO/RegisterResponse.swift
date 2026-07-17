//
//  RegisterResponse.swift
//  AuthFeature
//
//  Created by Pavel Guzenko on 16.07.2025.
//  Copyright © 2025 Eltex. All rights reserved.
//

import Foundation

/// Ответ на регистрацию.
internal struct RegisterResponse: Decodable {

    let email: String
}
