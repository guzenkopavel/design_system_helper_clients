import Foundation

public struct MyProfileAccount: Equatable, Sendable {

    public let email: String

    public init(email: String) {
        self.email = email
    }
}

public struct MyProfileSummary: Equatable, Sendable {

    public let email: String
    public let interviewCount: Int

    public var isMyInterviewsEnabled: Bool {
        interviewCount > 0
    }

    public init(email: String, interviewCount: Int) {
        self.email = email
        self.interviewCount = interviewCount
    }
}

public enum MyProfileFeatureError: Error, Equatable, Sendable {
    case invalidSession
    case offline
    case backend
    case decoding
}

public enum MyProfileState: Equatable, Sendable {
    case idle
    case loading
    case loaded(MyProfileSummary)
    case historyFailed(email: String, message: String)
    case signingOut(MyProfileSummary?)
    case logoutFailed(MyProfileSummary, message: String)
    case signedOut
    case invalidSession
}
