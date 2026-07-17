//
//  DefaultLogInUseCase.swift
//  AuthFeature
//
//  Created by Pavel Guzenko on 16.07.2025.
//  Copyright © 2025 Eltex. All rights reserved.
//

/// Реализация входа существующего аккаунта.
internal struct DefaultLogInUseCase: LogInUseCase {

    private let client: AuthAPIClient
    private let store: SessionSecretStore

    internal init(client: AuthAPIClient, store: SessionSecretStore) {
        self.client = client
        self.store = store
    }

    internal func execute(email: String, password: String) async throws -> String {
        let token = try await client.login(email: email, password: password)
        try await store.save(token)
        return token
    }
}
