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
        #expect(source.contains("profileContent"))
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
        #expect(!source.contains("URLSession"))
        #expect(!source.contains("/api/profile"))
        #expect(!source.contains("/api/interviews/history"))
    }

    @Test func profilePackageIsComposedThroughPublicBoundary() throws {
        let contentSource = try contentViewSource()
        let applicationSource = try appSource(named: "SysDevScenApp.swift")
        let rootSource = try appSource(named: "RootView.swift")

        #expect(!contentSource.contains("import MyProfileFeature"))
        #expect(!contentSource.contains("MyProfileView("))
        #expect(!contentSource.contains("MyProfileStateStore"))
        #expect(applicationSource.contains("profileFactory.makeProfileView"))
        #expect(applicationSource.contains("profileFactory.makePreviewSessionClient(arguments: arguments)"))
        #expect(!applicationSource.contains("StubProfileSessionClient"))
        #expect(!applicationSource.contains("AuthSessionRequest.profile()"))
        #expect(!applicationSource.contains("AuthSessionRequest.interviewHistory()"))
        #expect(!applicationSource.contains("AuthSessionRequest.logout()"))
        #expect(!applicationSource.contains("MyProfileFeatureFactory().makeStateStore"))
        #expect(!applicationSource.contains("/api/profile"))
        #expect(!applicationSource.contains("/api/interviews/history"))
        #expect(applicationSource.contains("authFactory.makeSessionRequestClient(configuration: configuration)"))
        #expect(applicationSource.contains("await sessionModel.invalidateSession()"))
        #expect(!rootSource.contains("await sessionModel.invalidateSession()"))
    }

    @Test func xcodeProjectLinksMyProfileProductOnlyToAppTarget() throws {
        let project = try projectSource()

        #expect(project.contains("XCLocalSwiftPackageReference \"../MyProfileFeature\""))
        #expect(project.contains("MyProfileFeature in Frameworks"))
        #expect(project.contains("productName = MyProfileFeature;"))
        #expect(project.contains("C0DEFACE0000000000000102 /* MyProfileFeature */,"))
        #expect(project.contains("C0DEFACE0000000000000103 /* XCLocalSwiftPackageReference \"../MyProfileFeature\" */"))
        #expect(!project.contains("SysDevScenTests */ = {\n\t\t\tisa = PBXNativeTarget;\n\t\t\tbuildConfigurationList = E95AEDAF3007A96C000B839E /* Build configuration list for PBXNativeTarget \"SysDevScenTests\" */;\n\t\t\tbuildPhases = (\n\t\t\t\tE95AED943007A96C000B839E /* Sources */,\n\t\t\t\tE95AED953007A96C000B839E /* Frameworks */,\n\t\t\t\tE95AED963007A96C000B839E /* Resources */,\n\t\t\t);\n\t\t\tbuildRules = (\n\t\t\t);\n\t\t\tdependencies = (\n\t\t\t\tE95AED9A3007A96C000B839E /* PBXTargetDependency */,\n\t\t\t);\n\t\t\tfileSystemSynchronizedGroups = (\n\t\t\t\tE95AED9B3007A96C000B839E /* SysDevScenTests */,\n\t\t\t);\n\t\t\tname = SysDevScenTests;\n\t\t\tpackageProductDependencies = (\n\t\t\t\tC0DEFACE0000000000000102 /* MyProfileFeature */"))
    }
}

private func contentViewSource() throws -> String {
    try appSource(named: "ContentView.swift")
}

private func appSource(named fileName: String) throws -> String {
    let testFile = URL(fileURLWithPath: #filePath)
    let projectRoot = testFile.deletingLastPathComponent().deletingLastPathComponent()
    let sourceURL = projectRoot.appendingPathComponent("SysDevScen/\(fileName)")
    return try String(contentsOf: sourceURL, encoding: .utf8)
}

private func projectSource() throws -> String {
    let testFile = URL(fileURLWithPath: #filePath)
    let projectRoot = testFile.deletingLastPathComponent().deletingLastPathComponent()
    let sourceURL = projectRoot.appendingPathComponent("SysDevScen.xcodeproj/project.pbxproj")
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
