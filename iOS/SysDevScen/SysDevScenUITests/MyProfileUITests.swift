//
//  MyProfileUITests.swift
//  SysDevScenUITests
//
//  Created by Codex on 17.07.2026.
//

import XCTest

final class MyProfileUITests: XCTestCase {
    private var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    override func tearDownWithError() throws {
        app = nil
    }

    @MainActor
    func testProfileTabShowsContentAndCountFeedbackWithoutNavigation() throws {
        launchProfile(arguments: ["--profile-stub-content"])

        XCTAssertTrue(app.staticTexts["pavel@example.com"].waitForExistence(timeout: 8))
        XCTAssertTrue(app.images["my-profile.symbol"].exists)
        XCTAssertTrue(app.buttons["Мои интервью"].exists)
        XCTAssertTrue(app.buttons["Выход"].exists)

        app.buttons["Мои интервью"].tap()

        XCTAssertTrue(app.staticTexts["Интервью: 3"].waitForExistence(timeout: 3))
        XCTAssertTrue(tab("Профиль").isSelected)
        XCTAssertFalse(app.navigationBars["Мои интервью"].exists)
    }

    @MainActor
    func testEmptyHistoryDisablesInterviewsAction() throws {
        launchProfile(arguments: ["--profile-stub-empty"])

        let button = app.buttons["Мои интервью"]
        XCTAssertTrue(button.waitForExistence(timeout: 8))
        XCTAssertFalse(button.isEnabled)
        XCTAssertFalse(app.staticTexts["Интервью: 0"].exists)
    }

    @MainActor
    func testHistoryErrorShowsRecoverableMessage() throws {
        launchProfile(arguments: ["--profile-stub-history-error"])

        XCTAssertTrue(app.staticTexts["Нет соединения"].waitForExistence(timeout: 8))
        XCTAssertFalse(app.buttons["Мои интервью"].isEnabled)
        XCTAssertTrue(tab("Профиль").isSelected)
    }

    @MainActor
    func testInvalidSessionReturnsToEmptyEmailEntry() throws {
        launchProfile(arguments: ["--profile-stub-invalid-session"])

        assertEmailEntryIsEmpty()
        XCTAssertFalse(app.staticTexts["pavel@example.com"].exists)
    }

    @MainActor
    func testLogoutReturnsToEmptyEmailEntry() throws {
        launchProfile(arguments: ["--profile-stub-content"])

        let logout = app.buttons["Выход"]
        XCTAssertTrue(logout.waitForExistence(timeout: 8))
        logout.tap()

        assertEmailEntryIsEmpty()
        XCTAssertFalse(app.staticTexts["pavel@example.com"].exists)
    }

    private func launchProfile(arguments: [String]) {
        app = XCUIApplication()
        app.launchArguments = ["--auth-stub-active"] + arguments
        app.launch()
        let profile = tab("Профиль")
        XCTAssertTrue(profile.waitForExistence(timeout: 8))
        profile.tap()
    }

    private func assertEmailEntryIsEmpty() {
        let email = app.textFields["auth.email"]
        XCTAssertTrue(email.waitForExistence(timeout: 8))
        XCTAssertEqual(email.value as? String, "Почта")
        XCTAssertFalse(app.staticTexts["existing@example.com"].exists)
        XCTAssertFalse(app.staticTexts["new-user@example.com"].exists)
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
