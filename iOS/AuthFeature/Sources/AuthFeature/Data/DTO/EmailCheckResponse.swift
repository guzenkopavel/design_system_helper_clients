//
//  EmailCheckResponse.swift
//  AuthFeature
//
//  Created by Pavel Guzenko on 16.07.2025.
//  Copyright © 2025 Eltex. All rights reserved.
//

import Foundation

/// Ответ на проверку существования почты.
internal struct EmailCheckResponse: Decodable {

    let exists: Bool
}
