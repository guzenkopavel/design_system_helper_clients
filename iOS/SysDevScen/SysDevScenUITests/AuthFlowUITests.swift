//
//  AuthFlowUITests.swift
//  SysDevScenUITests
//
//  Created by Codex on 17.07.2026.
//

import XCTest

final class AuthFlowUITests: XCTestCase {
    private var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["--auth-stub-signed-out"]
        app.launch()
    }

    override func tearDownWithError() throws {
        app = nil
    }

    @MainActor
    func testSignedOutLaunchShowsEmailStepAndHidesShell() throws {
        XCTAssertTrue(emailField.waitForExistence(timeout: 8))
        XCTAssertTrue(continueButton.exists)
        XCTAssertTrue(app.staticTexts["Авторизация"].exists || app.navigationBars["Почта"].exists)
        XCTAssertFalse(app.tabBars.buttons["Кейсы"].exists)
        XCTAssertFalse(app.tabBars.buttons["Знания"].exists)
        XCTAssertFalse(app.tabBars.buttons["Профиль"].exists)
    }

    @MainActor
    func testExistingEmailBranchesToLoginStep() throws {
        submitEmail("existing@example.com")

        XCTAssertTrue(waitForTitle("Вход"))
        XCTAssertTrue(passwordField.waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["auth.confirmed-email"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["existing@example.com"].exists)
    }

    @MainActor
    func testNewEmailBranchesToRegistrationStep() throws {
        submitEmail("new-user@example.com")

        XCTAssertTrue(waitForTitle("Регистрация"))
        XCTAssertTrue(passwordField.waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["auth.confirmed-email"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["new-user@example.com"].exists)
    }

    @MainActor
    func testBackToEmailPreservesEnteredEmail() throws {
        submitEmail("existing@example.com")
        XCTAssertTrue(waitForTitle("Вход"))

        app.buttons["auth.back-to-email"].tap()

        XCTAssertTrue(emailField.waitForExistence(timeout: 5))
        XCTAssertEqual(emailField.value as? String, "existing@example.com")
    }

    @MainActor
    func testSuccessfulLoginOpensCasesShell() throws {
        submitEmail("existing@example.com")
        XCTAssertTrue(waitForTitle("Вход"))

        submitPassword("password123")

        XCTAssertTrue(app.tabBars.buttons["Кейсы"].waitForExistence(timeout: 15))
        XCTAssertTrue(app.staticTexts["Кейсы"].exists)
    }

    @MainActor
    func testSuccessfulRegistrationOpensCasesShell() throws {
        submitEmail("new-user@example.com")
        XCTAssertTrue(waitForTitle("Регистрация"))

        submitPassword("password123")

        XCTAssertTrue(app.tabBars.buttons["Кейсы"].waitForExistence(timeout: 15))
        XCTAssertTrue(app.staticTexts["Кейсы"].exists)
    }

    private var emailField: XCUIElement {
        app.textFields["auth.email"]
    }

    private var continueButton: XCUIElement {
        app.buttons["auth.continue"]
    }

    private var passwordField: XCUIElement {
        let secureField = app.secureTextFields["auth.password"]
        if secureField.exists {
            return secureField
        }
        return app.textFields["auth.password"]
    }

    private func submitEmail(_ email: String) {
        XCTAssertTrue(emailField.waitForExistence(timeout: 8))
        emailField.tap()
        emailField.typeText(email)
        continueButton.tap()
    }

    private func submitPassword(_ password: String) {
        let visibilityButton = app.buttons["auth.password-visibility"]
        XCTAssertTrue(visibilityButton.waitForExistence(timeout: 5))
        visibilityButton.tap()

        let visiblePasswordField = app.textFields["auth.password"]
        XCTAssertTrue(visiblePasswordField.waitForExistence(timeout: 5))
        visiblePasswordField.tap()
        visiblePasswordField.typeText(password)

        let submitButton = app.buttons["auth.submit-password"]
        XCTAssertTrue(submitButton.waitForExistence(timeout: 5))
        if !submitButton.isHittable {
            app.swipeUp()
        }
        XCTAssertTrue(submitButton.waitForExistence(timeout: 5))
        submitButton.tap()
    }

    private func waitForTitle(_ title: String) -> Bool {
        app.staticTexts[title].waitForExistence(timeout: 5)
            || app.navigationBars[title].waitForExistence(timeout: 2)
    }
}
