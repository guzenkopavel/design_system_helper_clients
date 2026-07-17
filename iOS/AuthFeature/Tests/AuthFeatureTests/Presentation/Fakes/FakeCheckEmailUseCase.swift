//
//  FakeCheckEmailUseCase.swift
//  AuthFeature
//
//  Created by Pavel Guzenko on 16.07.2025.
//  Copyright © 2025 Eltex. All rights reserved.
//

@testable import AuthFeature

final class FakeCheckEmailUseCase: @unchecked Sendable, CheckEmailUseCase {

    var result: Result<Bool, Error> = .failure(AuthError.offline)
    var callCount = 0

    func execute(_ email: String) async throws -> Bool {
        callCount += 1
        return try result.get()
    }
}
