protocol MyProfileRepository: Sendable {

    func fetchProfile() async throws -> MyProfileAccount
    func fetchInterviewCount() async throws -> Int
    func logout() async throws
}
