//
//  SysDevScenApp.swift
//  SysDevScen
//
//  Created by pavel on 15.07.2026.
//

import AuthFeature
import Foundation
import SwiftUI

@main
struct SysDevScenApp: App {
    @StateObject private var sessionModel: AuthSessionModel

    @MainActor
    init() {
        _sessionModel = StateObject(wrappedValue: Self.makeSessionModel())
    }

    var body: some Scene {
        WindowGroup {
            RootView(sessionModel: sessionModel)
        }
    }

    @MainActor
    private static func makeSessionModel() -> AuthSessionModel {
        let factory = AuthFeatureFactory()
        let arguments = ProcessInfo.processInfo.arguments

        if arguments.contains("--auth-stub-active") {
            return factory.makeStubSessionModel(scenario: .active)
        }

        if arguments.contains("--auth-stub-invalid-session") {
            return factory.makeStubSessionModel(scenario: .invalidSession)
        }

        if arguments.contains("--auth-stub-signed-out") {
            return factory.makeStubSessionModel(scenario: .signedOut)
        }

        let rawBaseURL = ProcessInfo.processInfo.environment["AUTH_API_BASE_URL"]
            ?? "https://89.125.1.21.nip.io"
        guard let apiBaseURL = URL(string: rawBaseURL),
              let configuration = try? AuthConfiguration(apiBaseURL: apiBaseURL) else {
            return factory.makeStubSessionModel(scenario: .signedOut)
        }

        return factory.makeSessionModel(configuration: configuration)
    }
}
