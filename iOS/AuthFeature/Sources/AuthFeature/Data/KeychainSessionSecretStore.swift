//
//  KeychainSessionSecretStore.swift
//  AuthFeature
//
//  Created by Pavel Guzenko on 16.07.2025.
//  Copyright © 2025 Eltex. All rights reserved.
//

import Foundation
import Security

/// Реализация SessionSecretStore через системный Keychain.
/// Секрет недоступен другим приложениям, без sharing-групп.
internal struct KeychainSessionSecretStore: SessionSecretStore {

    private let service: String = "ru.home.sysdevsc.dsh"
    private let account: String = "dsh_session"

    internal func save(_ secret: String) async throws {
        let data = secret.data(using: .utf8)!

        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly,
            kSecValueData as String: data
        ]

        // Удалить предыдущее значение, если существует
        SecItemDelete(query as CFDictionary)

        let status = SecItemAdd(query as CFDictionary, nil)
        guard status == errSecSuccess else {
            throw KeychainError.saveFailed(status: Int(status))
        }
    }

    internal func load() async throws -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]

        var result: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        guard status == errSecSuccess, let data = result as? Data else {
            return nil
        }

        return String(data: data, encoding: .utf8)
    }

    internal func remove() async throws {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account
        ]

        let status = SecItemDelete(query as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else {
            throw KeychainError.deleteFailed(status: Int(status))
        }
    }
}

/// Внутренние ошибки Keychain.
private enum KeychainError: Error, Sendable {
    case saveFailed(status: Int)
    case deleteFailed(status: Int)
}
