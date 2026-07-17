//
//  KeychainSessionSecretStoreTests.swift
//  AuthFeature
//
//  Created by Pavel Guzenko on 16.07.2025.
//  Copyright © 2025 Eltex. All rights reserved.
//

@testable import AuthFeature
import XCTest

final class KeychainSessionSecretStoreTests: XCTestCase {

    private var store: InMemorySessionSecretStore!

    override func setUp() {
        super.setUp()
        store = InMemorySessionSecretStore()
    }

    override func tearDown() {
        store = nil
        super.tearDown()
    }

    func test_load_emptyReturnsNil() async throws {
        let result = try await store.load()
        XCTAssertNil(result)
    }

    func test_save_load_roundTrip() async throws {
        try await store.save("abc123")
        let result = try await store.load()
        XCTAssertEqual(result, "abc123")
    }

    func test_save_overwritesPrevious() async throws {
        try await store.save("old")
        try await store.save("new")
        let result = try await store.load()
        XCTAssertEqual(result, "new")
    }

    func test_remove_clearsSecret() async throws {
        try await store.save("secret")
        try await store.remove()
        let result = try await store.load()
        XCTAssertNil(result)
    }

    func test_remove_idempotent() async throws {
        try await store.remove()
        try await store.remove()
        // Не должно бросать ошибку
    }

    func test_remove_then_load_returnsNil() async throws {
        try await store.save("present")
        try await store.remove()
        let result = try await store.load()
        XCTAssertNil(result)
    }
}
