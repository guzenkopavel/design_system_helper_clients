import Foundation

struct MyProfileStrings: Sendable {

    static let shared = MyProfileStrings()

    let myInterviews = "Мои интервью"
    let logout = "Выход"
    let loading = "Загрузка профиля"
    let profileEmailLabel = "Email текущего профиля"
    let profileSymbolLabel = "Профиль"
    let myInterviewsDisabledHint = "Недоступно, пока нет интервью или счётчик неизвестен"
    let myInterviewsEnabledHint = "Показывает количество интервью без перехода на другой экран"
    let logoutInProgress = "Выполняется выход"
    let retry = "Повторить"
    let historyUnavailable = "Не удалось загрузить историю"
    let offline = "Нет соединения"
    let logoutFailed = "Не удалось выйти"

    func interviewCountMessage(_ count: Int) -> String {
        String(format: "Интервью: %d", locale: Locale(identifier: "ru_RU"), count)
    }
}
