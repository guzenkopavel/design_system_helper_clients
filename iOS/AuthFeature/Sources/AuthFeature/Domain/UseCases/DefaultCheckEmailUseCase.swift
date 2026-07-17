//
//  DefaultCheckEmailUseCase.swift
//  AuthFeature
//
//  Created by Pavel Guzenko on 16.07.2025.
//  Copyright © 2025 Eltex. All rights reserved.
//

/// Реализация проверки существования почты.
internal struct DefaultCheckEmailUseCase: CheckEmailUseCase {

    private let client: AuthAPIClient

    internal init(client: AuthAPIClient) {
        self.client = client
    }

    internal func execute(_ email: String) async throws -> Bool {
        try await client.checkEmail(email)
    }
}
