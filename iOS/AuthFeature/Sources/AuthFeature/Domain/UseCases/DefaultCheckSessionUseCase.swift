//
//  DefaultCheckSessionUseCase.swift
//  AuthFeature
//
//  Created by Pavel Guzenko on 16.07.2025.
//  Copyright © 2025 Eltex. All rights reserved.
//

/// Реализация проверки валидности серверной сессии.
internal struct DefaultCheckSessionUseCase: CheckSessionUseCase {

    private let client: AuthAPIClient
    private let store: SessionSecretStore

    internal init(client: AuthAPIClient, store: SessionSecretStore) {
        self.client = client
        self.store = store
    }

    internal func execute() async throws -> Bool {
        let token = try await store.load()

        guard let token = token else {
            return false
        }

        do {
            let isValid = try await client.checkSession(token: token)
            return isValid
        } catch {
            if case AuthError.sessionInvalid = error {
                try await store.remove()
                return false
            }
            throw error
        }
    }
}
