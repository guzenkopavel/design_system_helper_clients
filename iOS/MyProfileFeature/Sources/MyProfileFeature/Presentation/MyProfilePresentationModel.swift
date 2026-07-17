import SwiftUI

struct MyProfilePresentationModel: Equatable, Sendable {

    let email: String?
    let isLoading: Bool
    let isLogoutLoading: Bool
    let isMyInterviewsEnabled: Bool
    let myInterviewsAccessibilityHint: String
    let statusMessage: String?
    let countFeedbackMessage: String?

    static func make(from state: MyProfileState) -> MyProfilePresentationModel {
        make(from: state, strings: .shared)
    }

    static func make(from state: MyProfileState, strings: MyProfileStrings) -> MyProfilePresentationModel {
        switch state {
        case .idle:
            return MyProfilePresentationModel(
                email: nil,
                isLoading: false,
                isLogoutLoading: false,
                isMyInterviewsEnabled: false,
                myInterviewsAccessibilityHint: strings.myInterviewsDisabledHint,
                statusMessage: nil,
                countFeedbackMessage: nil
            )
        case .loading:
            return MyProfilePresentationModel(
                email: nil,
                isLoading: true,
                isLogoutLoading: false,
                isMyInterviewsEnabled: false,
                myInterviewsAccessibilityHint: strings.myInterviewsDisabledHint,
                statusMessage: strings.loading,
                countFeedbackMessage: nil
            )
        case let .loaded(summary):
            return loaded(summary, strings: strings, statusMessage: nil)
        case let .historyFailed(email, message):
            return MyProfilePresentationModel(
                email: email.isEmpty ? nil : email,
                isLoading: false,
                isLogoutLoading: false,
                isMyInterviewsEnabled: false,
                myInterviewsAccessibilityHint: strings.myInterviewsDisabledHint,
                statusMessage: message.isEmpty ? strings.historyUnavailable : message,
                countFeedbackMessage: nil
            )
        case let .signingOut(summary):
            return MyProfilePresentationModel(
                email: summary?.email,
                isLoading: false,
                isLogoutLoading: true,
                isMyInterviewsEnabled: false,
                myInterviewsAccessibilityHint: strings.myInterviewsDisabledHint,
                statusMessage: strings.logoutInProgress,
                countFeedbackMessage: nil
            )
        case let .logoutFailed(summary, message):
            return loaded(
                summary,
                strings: strings,
                statusMessage: message.isEmpty ? strings.logoutFailed : message
            )
        case .signedOut, .invalidSession:
            return MyProfilePresentationModel(
                email: nil,
                isLoading: false,
                isLogoutLoading: false,
                isMyInterviewsEnabled: false,
                myInterviewsAccessibilityHint: strings.myInterviewsDisabledHint,
                statusMessage: nil,
                countFeedbackMessage: nil
            )
        }
    }

    static func countFeedback(for state: MyProfileState) -> String? {
        countFeedback(for: state, strings: .shared)
    }

    static func countFeedback(for state: MyProfileState, strings: MyProfileStrings) -> String? {
        guard case let .loaded(summary) = state, summary.interviewCount > 0 else {
            return nil
        }
        return strings.interviewCountMessage(summary.interviewCount)
    }

    private static func loaded(
        _ summary: MyProfileSummary,
        strings: MyProfileStrings,
        statusMessage: String?
    ) -> MyProfilePresentationModel {
        MyProfilePresentationModel(
            email: summary.email,
            isLoading: false,
            isLogoutLoading: false,
            isMyInterviewsEnabled: summary.isMyInterviewsEnabled,
            myInterviewsAccessibilityHint: summary.isMyInterviewsEnabled
                ? strings.myInterviewsEnabledHint
                : strings.myInterviewsDisabledHint,
            statusMessage: statusMessage,
            countFeedbackMessage: summary.isMyInterviewsEnabled
                ? strings.interviewCountMessage(summary.interviewCount)
                : nil
        )
    }
}

struct MyProfileVisualEnvironment: Equatable, Sendable {

    let colorScheme: ColorScheme
    let contrast: MyProfileContrast
    let reduceMotion: Bool
    let reduceTransparency: Bool

    init(
        colorScheme: ColorScheme,
        contrast: MyProfileContrast,
        reduceMotion: Bool,
        reduceTransparency: Bool
    ) {
        self.colorScheme = colorScheme
        self.contrast = contrast
        self.reduceMotion = reduceMotion
        self.reduceTransparency = reduceTransparency
    }

    var usesTransparencyFallback: Bool {
        reduceTransparency
    }

    var feedbackAnimation: Animation? {
        reduceMotion ? nil : .easeInOut(duration: 0.2)
    }

    var profileSymbolName: String {
        "person.crop.circle.fill"
    }
}

enum MyProfileContrast: Equatable, Sendable {
    case normal
    case increased
}
