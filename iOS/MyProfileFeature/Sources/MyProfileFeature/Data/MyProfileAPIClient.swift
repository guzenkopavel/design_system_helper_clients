import AuthFeature
import Foundation

public struct MyProfileFeatureFactory: Sendable {

    public init() {}

    @MainActor
    func makeStateStore(
        sessionClient: any AuthSessionRequesting,
        recoverInvalidSession: @escaping @MainActor @Sendable () async -> Void
    ) -> MyProfileStateStore {
        MyProfileStateStore(
            repository: MyProfileAPIClient(sessionClient: sessionClient),
            recoverInvalidSession: recoverInvalidSession
        )
    }
}

struct MyProfileAPIClient: MyProfileRepository {

    private let sessionClient: any AuthSessionRequesting
    private let decoder: JSONDecoder
    private let pageSize: Int

    init(
        sessionClient: any AuthSessionRequesting,
        decoder: JSONDecoder = JSONDecoder(),
        pageSize: Int = 20
    ) {
        self.sessionClient = sessionClient
        self.decoder = decoder
        self.pageSize = pageSize
    }

    func fetchProfile() async throws -> MyProfileAccount {
        do {
            let response = try await sessionClient.execute(.profile())
            let dto = try decoder.decode(ProfileDTO.self, from: response.data)
            return MyProfileAccount(email: dto.email)
        } catch {
            throw map(error)
        }
    }

    func fetchInterviewCount() async throws -> Int {
        var page = 1
        var count = 0

        while true {
            try Task.checkCancellation()
            let response: AuthSessionResponse
            do {
                response = try await sessionClient.execute(.interviewHistory(page: page, pageSize: pageSize))
            } catch {
                throw map(error)
            }

            do {
                let dto = try decoder.decode(InterviewHistoryListDTO.self, from: response.data)
                count += dto.data.count
                guard dto.page.hasMore else {
                    return count
                }
                page += 1
            } catch is CancellationError {
                throw CancellationError()
            } catch {
                throw MyProfileFeatureError.decoding
            }
        }
    }

    func logout() async throws {
        do {
            _ = try await sessionClient.execute(.logout())
        } catch {
            throw map(error)
        }
    }

    private func map(_ error: Error) -> MyProfileFeatureError {
        if let profileError = error as? MyProfileFeatureError {
            return profileError
        }
        if let requestError = error as? AuthSessionRequestError {
            switch requestError {
            case .invalidSession:
                return .invalidSession
            default:
                return .backend
            }
        }
        if let urlError = error as? URLError,
           [.notConnectedToInternet, .networkConnectionLost, .timedOut].contains(urlError.code) {
            return .offline
        }
        return .backend
    }
}

private struct ProfileDTO: Decodable {
    let email: String
}

private struct InterviewHistoryListDTO: Decodable {
    let data: [InterviewDTO]
    let page: PageDTO
}

private struct InterviewDTO: Decodable {}

private struct PageDTO: Decodable {
    let hasMore: Bool
}
