//
//  AppShellUITests.swift
//  SysDevScenUITests
//
//  Created by pavel on 15.07.2026.
//

import XCTest

final class AppShellUITests: XCTestCase {
    private var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["--auth-stub-active"]
        app.launch()
    }

    override func tearDownWithError() throws {
        app = nil
    }

    @MainActor
    func testLaunchShowsCasesFirstAndKeepsNavigationAvailable() throws {
        let cases = tab("Кейсы")
        let knowledge = tab("Знания")
        let profile = tab("Профиль")

        XCTAssertTrue(cases.waitForExistence(timeout: 5))
        XCTAssertTrue(knowledge.exists)
        XCTAssertTrue(profile.exists)
        XCTAssertTrue(app.staticTexts["Кейсы"].exists)
        XCTAssertTrue(cases.isSelected)
        XCTAssertFalse(knowledge.isSelected)
        XCTAssertFalse(profile.isSelected)
    }

    @MainActor
    func testSelectionMovesBetweenAllSectionsWithoutTemplateControls() throws {
        tapTab("Знания")
        XCTAssertTrue(app.staticTexts["Знания"].waitForExistence(timeout: 2))
        XCTAssertTrue(tab("Знания").isSelected)
        XCTAssertTrue(tab("Кейсы").exists)
        XCTAssertTrue(tab("Профиль").exists)

        tapTab("Профиль")
        XCTAssertTrue(app.staticTexts["pavel@example.com"].waitForExistence(timeout: 5))
        XCTAssertTrue(tab("Профиль").isSelected)

        tapTab("Кейсы")
        XCTAssertTrue(app.staticTexts["Кейсы"].waitForExistence(timeout: 2))
        XCTAssertTrue(tab("Кейсы").isSelected)

        XCTAssertFalse(app.buttons["Add Item"].exists)
        XCTAssertFalse(app.buttons["Edit"].exists)
        XCTAssertFalse(app.staticTexts["Select an item"].exists)
    }

    @MainActor
    func testRepeatedSelectionDoesNotHideShellNavigation() throws {
        tapTab("Кейсы")
        tapTab("Кейсы")

        XCTAssertTrue(app.staticTexts["Кейсы"].exists)
        XCTAssertTrue(tab("Кейсы").isSelected)
        XCTAssertTrue(tab("Знания").exists)
        XCTAssertTrue(tab("Профиль").exists)
    }

    private func tapTab(_ title: String) {
        let element = tab(title)
        XCTAssertTrue(element.waitForExistence(timeout: 5))
        element.tap()
    }

    private func tab(_ title: String) -> XCUIElement {
        let predicate = NSPredicate(format: "label == %@ OR identifier == %@", title, title)
        let candidates = [
            app.tabBars.buttons.matching(predicate).firstMatch,
            app.buttons.matching(predicate).firstMatch,
            app.cells.matching(predicate).firstMatch,
            app.otherElements.matching(predicate).firstMatch,
            app.descendants(matching: .any).matching(predicate).firstMatch,
        ]
        return candidates.first(where: \.exists) ?? candidates[candidates.count - 1]
    }
}
