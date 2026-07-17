//
//  ContentView.swift
//  SysDevScen
//
//  Created by pavel on 15.07.2026.
//

import SwiftUI

struct ContentView: View {
    let profileContent: AnyView

    var body: some View {
        RootShellView(profileContent: profileContent)
    }
}

private struct RootShellView: View {
    let profileContent: AnyView

    @State private var selectedSection: RootSection = .cases

    var body: some View {
        TabView(selection: $selectedSection) {
            ForEach(RootSection.allCases) { section in
                sectionContent(section)
                    .tag(section)
                    .tabItem { Label(section.title, systemImage: section.systemImage) }
            }
        }
    }

    @ViewBuilder
    private func sectionContent(_ section: RootSection) -> some View {
        switch section {
        case .cases, .knowledge:
            ContentUnavailableView(section.title, systemImage: section.systemImage)
                .accessibilityIdentifier(section.contentIdentifier)
        case .profile:
            profileContent
                .accessibilityIdentifier(section.contentIdentifier)
        }
    }
}

private enum RootSection: String, CaseIterable, Identifiable {
    case cases
    case knowledge
    case profile

    var id: Self { self }

    var title: String {
        switch self {
        case .cases:
            "Кейсы"
        case .knowledge:
            "Знания"
        case .profile:
            "Профиль"
        }
    }

    var systemImage: String {
        switch self {
        case .cases:
            "tray.full"
        case .knowledge:
            "book"
        case .profile:
            "person.crop.circle"
        }
    }

    var contentIdentifier: String {
        switch self {
        case .cases:
            "root-section-cases"
        case .knowledge:
            "root-section-knowledge"
        case .profile:
            "root-section-profile"
        }
    }
}

#Preview {
    ContentView(
        profileContent: AnyView(Text("Профиль"))
    )
}
