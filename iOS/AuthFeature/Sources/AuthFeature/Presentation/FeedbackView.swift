#if os(iOS)
import SwiftUI

struct FeedbackView: View {

    let feedback: AuthFlowState.Feedback
    let onRetry: () -> Void

    @ViewBuilder
    var body: some View {
        switch feedback {
        case .none:
            EmptyView()
        case .inputWarning(let message):
            feedbackLabel(message, systemImage: "exclamationmark.circle")
        case .credentialsError:
            feedbackLabel("Проверьте почту и пароль.", systemImage: "exclamationmark.triangle")
        case .emailTaken:
            feedbackLabel(
                "Аккаунт с этой почтой уже существует. Вернитесь к почте и выполните вход.",
                systemImage: "person.crop.circle.badge.exclamationmark"
            )
        case .serverError:
            feedbackLabel("Не удалось выполнить запрос. Повторите попытку.", systemImage: "exclamationmark.triangle")
        case .rateLimited(let retryAfter):
            TimelineView(.periodic(from: .now, by: 1)) { context in
                VStack(alignment: .leading) {
                    feedbackLabel(
                        rateLimitMessage(until: retryAfter, now: context.date),
                        systemImage: "clock.badge.exclamationmark"
                    )
                    Button("Повторить", action: onRetry)
                        .buttonStyle(.bordered)
                        .disabled(context.date < retryAfter)
                        .accessibilityLabel("Повторить")
                        .accessibilityIdentifier("auth.retry")
                }
            }
        case .offline:
            VStack(alignment: .leading) {
                feedbackLabel("Нет подключения к сети.", systemImage: "wifi.exclamationmark")
                Button("Повторить", action: onRetry)
                    .buttonStyle(.bordered)
                    .accessibilityLabel("Повторить")
                    .accessibilityIdentifier("auth.retry")
            }
        }
    }

    private func feedbackLabel(_ message: String, systemImage: String) -> some View {
        Label(message, systemImage: systemImage)
            .fixedSize(horizontal: false, vertical: true)
            .accessibilityElement(children: .combine)
            .accessibilityLabel(message)
            .accessibilityAddTraits(.isStaticText)
            .accessibilityIdentifier("auth.feedback")
    }

    private func rateLimitMessage(until retryAfter: Date, now: Date) -> String {
        let seconds = max(0, Int(retryAfter.timeIntervalSince(now).rounded(.up)))
        return seconds > 0
            ? "Слишком много попыток. Повторите через \(seconds) секунд."
            : "Можно повторить попытку."
    }
}

extension AuthFlowState.Feedback {
    var accessibilityAnnouncement: String? {
        switch self {
        case .none:
            return nil
        case .inputWarning(let message):
            return message
        case .credentialsError:
            return "Проверьте почту и пароль."
        case .emailTaken:
            return "Аккаунт с этой почтой уже существует. Вернитесь к почте и выполните вход."
        case .serverError:
            return "Не удалось выполнить запрос. Повторите попытку."
        case .rateLimited(let retryAfter):
            let seconds = max(0, Int(retryAfter.timeIntervalSinceNow.rounded(.up)))
            return "Слишком много попыток. Повторите через \(seconds) секунд."
        case .offline:
            return "Нет подключения к сети. Доступно действие Повторить."
        }
    }

    var blocksPrimaryAction: Bool {
        if case .rateLimited = self {
            return true
        }
        return false
    }
}
#endif
