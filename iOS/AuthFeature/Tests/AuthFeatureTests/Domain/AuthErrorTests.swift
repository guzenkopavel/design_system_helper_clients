@testable import AuthFeature
import XCTest

final class AuthErrorTests: XCTestCase {

    func authError_hasAllExpectedCases() {
        let allCases: [AuthError] = [
            .invalidInput(message: "test"),
            .emailAlreadyRegistered,
            .serverValidation(message: "test"),
            .rateLimited(retryAfter: Date()),
            .offline,
            .sessionInvalid,
            .backendFailure(traceID: nil),
            .invalidConfiguration,
        ]
        XCTAssertEqual(allCases.count, 8)
    }
}
