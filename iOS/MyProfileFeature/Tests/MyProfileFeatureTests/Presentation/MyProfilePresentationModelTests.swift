@testable import MyProfileFeature
import SwiftUI
import XCTest

final class MyProfilePresentationModelTests: XCTestCase {

    func test_loadedWithInterviewCount_enablesActionAndBuildsFeedback() {
        let state = MyProfileState.loaded(MyProfileSummary(email: "pavel@example.com", interviewCount: 3))

        let model = MyProfilePresentationModel.make(from: state)

        XCTAssertEqual(model.email, "pavel@example.com")
        XCTAssertTrue(model.isMyInterviewsEnabled)
        XCTAssertEqual(model.countFeedbackMessage, "Интервью: 3")
        XCTAssertEqual(MyProfilePresentationModel.countFeedback(for: state), "Интервью: 3")
    }

    func test_loadedWithEmptyHistory_disablesActionWithoutFeedback() {
        let state = MyProfileState.loaded(MyProfileSummary(email: "pavel@example.com", interviewCount: 0))

        let model = MyProfilePresentationModel.make(from: state)

        XCTAssertFalse(model.isMyInterviewsEnabled)
        XCTAssertNil(model.countFeedbackMessage)
        XCTAssertEqual(model.myInterviewsAccessibilityHint, "Недоступно, пока нет интервью или счётчик неизвестен")
    }

    func test_signingOutDisablesActionsAndAnnouncesBusyState() {
        let state = MyProfileState.signingOut(MyProfileSummary(email: "pavel@example.com", interviewCount: 2))

        let model = MyProfilePresentationModel.make(from: state)

        XCTAssertEqual(model.email, "pavel@example.com")
        XCTAssertTrue(model.isLogoutLoading)
        XCTAssertFalse(model.isMyInterviewsEnabled)
        XCTAssertEqual(model.statusMessage, "Выполняется выход")
    }

    func test_historyFailureKeepsEmailAndDisablesInterviewAction() {
        let state = MyProfileState.historyFailed(email: "pavel@example.com", message: "Нет соединения")

        let model = MyProfilePresentationModel.make(from: state)

        XCTAssertEqual(model.email, "pavel@example.com")
        XCTAssertFalse(model.isMyInterviewsEnabled)
        XCTAssertEqual(model.statusMessage, "Нет соединения")
    }

    func test_visualEnvironmentBranchesForTransparencyMotionAndSymbol() {
        let reduced = MyProfileVisualEnvironment(
            colorScheme: .dark,
            contrast: .increased,
            reduceMotion: true,
            reduceTransparency: true
        )

        XCTAssertTrue(reduced.usesTransparencyFallback)
        XCTAssertNil(reduced.feedbackAnimation)
        XCTAssertEqual(reduced.profileSymbolName, "person.crop.circle.fill")

        let standard = MyProfileVisualEnvironment(
            colorScheme: .light,
            contrast: .normal,
            reduceMotion: false,
            reduceTransparency: false
        )

        XCTAssertFalse(standard.usesTransparencyFallback)
        XCTAssertNotNil(standard.feedbackAnimation)
    }

    func test_russianStringsComeFromResources() {
        let strings = MyProfileStrings.shared

        XCTAssertEqual(strings.myInterviews, "Мои интервью")
        XCTAssertEqual(strings.logout, "Выход")
        XCTAssertEqual(strings.interviewCountMessage(7), "Интервью: 7")
        XCTAssertFalse(strings.myInterviewsDisabledHint.contains("%"))
        XCTAssertTrue(localizedResourceText().contains("\"my_profile_logout\" = \"Выход\";"))
        XCTAssertTrue(localizedResourceText().contains("\"my_profile_interview_count_format\" = \"Интервью: %d\";"))
    }

    private func localizedResourceText() -> String {
        let current = URL(fileURLWithPath: #filePath)
        let packageRoot = current
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
        let resource = packageRoot
            .appendingPathComponent("Sources/MyProfileFeature/Resources/Localizable.ru.strings")
        return (try? String(contentsOf: resource, encoding: .utf8)) ?? ""
    }
}
