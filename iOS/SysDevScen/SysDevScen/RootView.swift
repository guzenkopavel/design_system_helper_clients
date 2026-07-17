//
//  RootView.swift
//  SysDevScen
//
//  Created by Codex on 17.07.2026.
//

import AuthFeature
import SwiftUI

struct RootView: View {
    @ObservedObject var sessionModel: AuthSessionModel

    var body: some View {
        Group {
            switch sessionModel.state {
            case .checking:
                ProgressView("Проверяем сессию")
                    .accessibilityIdentifier("auth.loading")
            case .signedOut:
                AuthFlowView(sessionModel: sessionModel)
            case .active:
                ContentView()
            }
        }
        .task {
            await sessionModel.start()
        }
    }
}

#Preview {
    RootView(sessionModel: AuthFeatureFactory().makeStubSessionModel(scenario: .active))
}
