//
//  SysDevScenApp.swift
//  SysDevScen
//
//  Created by pavel on 15.07.2026.
//

import AuthFeature
import Foundation
import MyProfileFeature
import SwiftUI

@main
struct SysDevScenApp: App {
    @StateObject private var sessionModel: AuthSessionModel
    private let profileContent: AnyView

    @MainActor
    init() {
        let dependencies = Self.makeDependencies()
        _sessionModel = StateObject(wrappedValue: dependencies.sessionModel)
        profileContent = dependencies.profileContent
    }

    var body: some Scene {
        WindowGroup {
            RootView(sessionModel: sessionModel, profileContent: profileContent)
        }
    }

    @MainActor
    private static func makeDependencies() -> AppDependencies {
        let authFactory = AuthFeatureFactory()
        let profileFactory = MyProfileFeatureFactory()
        let arguments = ProcessInfo.processInfo.arguments

        if arguments.contains("--auth-stub-active") {
            let sessionModel = authFactory.makeStubSessionModel(scenario: .active)
            return AppDependencies(
                sessionModel: sessionModel,
                profileContent: makeProfileContent(
                    profileFactory: profileFactory,
                    sessionClient: profileFactory.makePreviewSessionClient(arguments: arguments),
                    sessionModel: sessionModel
                )
            )
        }

        if arguments.contains("--auth-stub-invalid-session") {
            let sessionModel = authFactory.makeStubSessionModel(scenario: .invalidSession)
            return AppDependencies(
                sessionModel: sessionModel,
                profileContent: makeProfileContent(
                    profileFactory: profileFactory,
                    sessionClient: profileFactory.makePreviewSessionClient(arguments: arguments),
                    sessionModel: sessionModel
                )
            )
        }

        if arguments.contains("--auth-stub-signed-out") {
            let sessionModel = authFactory.makeStubSessionModel(scenario: .signedOut)
            return AppDependencies(
                sessionModel: sessionModel,
                profileContent: makeProfileContent(
                    profileFactory: profileFactory,
                    sessionClient: profileFactory.makePreviewSessionClient(arguments: arguments),
                    sessionModel: sessionModel
                )
            )
        }

        let rawBaseURL = ProcessInfo.processInfo.environment["AUTH_API_BASE_URL"]
            ?? "https://89.125.1.21.nip.io"
        guard let apiBaseURL = URL(string: rawBaseURL),
              let configuration = try? AuthConfiguration(apiBaseURL: apiBaseURL) else {
            let sessionModel = authFactory.makeStubSessionModel(scenario: .signedOut)
            return AppDependencies(
                sessionModel: sessionModel,
                profileContent: makeProfileContent(
                    profileFactory: profileFactory,
                    sessionClient: profileFactory.makePreviewSessionClient(arguments: ["--auth-stub-signed-out"]),
                    sessionModel: sessionModel
                )
            )
        }

        let sessionModel = authFactory.makeSessionModel(configuration: configuration)
        return AppDependencies(
            sessionModel: sessionModel,
            profileContent: makeProfileContent(
                profileFactory: profileFactory,
                sessionClient: authFactory.makeSessionRequestClient(configuration: configuration),
                sessionModel: sessionModel
            )
        )
    }

    @MainActor
    private static func makeProfileContent(
        profileFactory: MyProfileFeatureFactory,
        sessionClient: any AuthSessionRequesting,
        sessionModel: AuthSessionModel
    ) -> AnyView {
        AnyView(
            profileFactory.makeProfileView(sessionClient: sessionClient) {
                await sessionModel.invalidateSession()
            }
        )
    }
}

private struct AppDependencies {
    let sessionModel: AuthSessionModel
    let profileContent: AnyView
}
