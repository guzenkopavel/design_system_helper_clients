//
//  InMemorySessionSecretStore.swift
//  AuthFeature
//
//  Created by Pavel Guzenko on 16.07.2025.
//  Copyright © 2025 Eltex. All rights reserved.
//

@testable import AuthFeature

/// Тестовая реализация хранилища в памяти.
final class InMemorySessionSecretStore: @unchecked Sendable, AuthFeature.SessionSecretStore {

    private var secret: String?

    init(initial: String? = nil) {
        self.secret = initial
    }

    nonisolated func save(_ newSecret: String) async throws {
        secret = newSecret
    }

    nonisolated func load() async throws -> String? {
        secret
    }

    nonisolated func remove() async throws {
        secret = nil
    }
}
