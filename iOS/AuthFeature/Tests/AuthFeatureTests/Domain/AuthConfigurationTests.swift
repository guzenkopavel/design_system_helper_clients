@testable import AuthFeature
import XCTest

final class AuthConfigurationTests: XCTestCase {

    func init_withHTTPSURL_succeeds() throws {
        let url = URL(string: "https://89.125.1.21.nip.io")!
        let config = try AuthConfiguration(apiBaseURL: url)
        XCTAssertEqual(config.apiBaseURL, url)
    }

    func init_withHTTPURL_throws() throws {
        let url = URL(string: "http://89.125.1.21.nip.io")!
        do {
            _ = try AuthConfiguration(apiBaseURL: url)
            XCTFail("Незащищённый адрес должен отклоняться")
        } catch AuthError.invalidConfiguration {
            // OK
        } catch {
            XCTFail("Ожидалась ошибка invalidConfiguration, получил \(error)")
        }
    }
}
