//
//  AppShellStateTests.swift
//  SysDevScenTests
//
//  Created by pavel on 15.07.2026.
//

import Foundation
import Testing

struct AppShellStateTests {
    @Test func rootSectionContractStaysClosedAndOrdered() throws {
        let source = try contentViewSource()

        #expect(source.contains("private enum RootSection"))
        #expect(orderedOffsets(of: ["case cases", "case knowledge", "case profile"], in: source) != nil)
        #expect(source.contains("@State private var selectedSection: RootSection = .cases"))
        #expect(source.contains("TabView(selection: $selectedSection)"))
    }

    @Test func rootSectionVisibleNamesMatchSharedOrder() throws {
        let source = try contentViewSource()

        #expect(orderedOffsets(of: ["\"Кейсы\"", "\"Знания\"", "\"Профиль\""], in: source) != nil)
        #expect(source.contains("Label(section.title, systemImage: section.systemImage)"))
        #expect(source.contains("ContentUnavailableView(section.title, systemImage: section.systemImage)"))
    }

    @Test func rootSectionUsesStableSystemSemanticsWithoutDataOwnership() throws {
        let source = try contentViewSource()

        #expect(source.contains("\"tray.full\""))
        #expect(source.contains("\"book\""))
        #expect(source.contains("\"person.crop.circle\""))
        #expect(source.contains("\"root-section-cases\""))
        #expect(source.contains("\"root-section-knowledge\""))
        #expect(source.contains("\"root-section-profile\""))
        #expect(!source.contains("CoreData"))
        #expect(!source.contains("managedObjectContext"))
        #expect(!source.contains("FetchRequest"))
        #expect(!source.contains("PersistenceController"))
        #expect(!source.contains("NavigationLink"))
    }
}

private func contentViewSource() throws -> String {
    let testFile = URL(fileURLWithPath: #filePath)
    let projectRoot = testFile.deletingLastPathComponent().deletingLastPathComponent()
    let sourceURL = projectRoot.appendingPathComponent("SysDevScen/ContentView.swift")
    return try String(contentsOf: sourceURL, encoding: .utf8)
}

private func orderedOffsets(of needles: [String], in haystack: String) -> [String.Index]? {
    var lowerBound = haystack.startIndex
    var offsets: [String.Index] = []

    for needle in needles {
        guard let range = haystack.range(of: needle, range: lowerBound..<haystack.endIndex) else {
            return nil
        }
        offsets.append(range.lowerBound)
        lowerBound = range.upperBound
    }

    return offsets
}
