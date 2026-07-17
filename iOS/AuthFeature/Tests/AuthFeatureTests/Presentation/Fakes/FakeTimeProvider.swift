//
//  FakeTimeProvider.swift
//  AuthFeature
//
//  Created by Pavel Guzenko on 16.07.2025.
//  Copyright © 2025 Eltex. All rights reserved.
//

@testable import AuthFeature
import Foundation

final class FakeTimeProvider: @unchecked Sendable, TimeProvider {

    private var _now: Date = Date()

    func now() -> Date { _now }

    func setNow(_ date: Date) {
        _now = date
    }
}
