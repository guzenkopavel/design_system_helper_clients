import Foundation

struct MyProfileAccount: Equatable, Sendable {

    let email: String

    init(email: String) {
        self.email = email
    }
}

struct MyProfileSummary: Equatable, Sendable {

    let email: String
    let interviewCount: Int

    var isMyInterviewsEnabled: Bool {
        interviewCount > 0
    }

    init(email: String, interviewCount: Int) {
        self.email = email
        self.interviewCount = interviewCount
    }
}

enum MyProfileFeatureError: Error, Equatable, Sendable {
    case invalidSession
    case offline
    case backend
    case decoding
}

enum MyProfileState: Equatable, Sendable {
    case idle
    case loading
    case loaded(MyProfileSummary)
    case historyFailed(email: String, message: String)
    case signingOut(MyProfileSummary?)
    case logoutFailed(MyProfileSummary, message: String)
    case signedOut
    case invalidSession
}
