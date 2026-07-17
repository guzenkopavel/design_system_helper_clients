//
//  FakeLogInUseCase.swift
//  AuthFeature
//
//  Created by Pavel Guzenko on 16.07.2025.
//  Copyright © 2025 Eltex. All rights reserved.
//

@testable import AuthFeature

final class FakeLogInUseCase: @unchecked Sendable, LogInUseCase {

    var result: Result<String, Error> = .success("login-token")
    var callCount = 0

    func execute(email: String, password: String) async throws -> String {
        callCount += 1
        return try result.get()
    }
}
