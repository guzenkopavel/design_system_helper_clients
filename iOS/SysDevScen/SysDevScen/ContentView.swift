//
//  ContentView.swift
//  SysDevScen
//
//  Created by pavel on 15.07.2026.
//

import SwiftUI

struct ContentView: View {
    var body: some View {
        RootShellView()
    }
}

private struct RootShellView: View {
    @State private var selectedSection: RootSection = .cases

    var body: some View {
        TabView(selection: $selectedSection) {
            ForEach(RootSection.allCases) { section in
                ContentUnavailableView(section.title, systemImage: section.systemImage)
                    .accessibilityIdentifier(section.contentIdentifier)
                    .tag(section)
                    .tabItem {
                        Label(section.title, systemImage: section.systemImage)
                    }
            }
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
    ContentView()
}
