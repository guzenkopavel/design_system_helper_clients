#if os(iOS)
import SwiftUI

struct PasswordStepView: View {

    @Binding var password: String

    let confirmedEmail: String
    let isLogin: Bool
    let showsPassword: Bool
    let feedback: AuthFlowState.Feedback
    let isLoading: Bool
    let isSubmissionBlocked: Bool
    let onSubmit: () -> Void
    let onRetry: () -> Void
    let onTogglePasswordVisibility: () -> Void
    let onBack: () -> Void

    @FocusState private var isPasswordFocused: Bool
    @AccessibilityFocusState private var isHeadingAccessibilityFocused: Bool

    private var title: String {
        isLogin ? "Вход" : "Регистрация"
    }

    private var primaryActionTitle: String {
        isLogin ? "Войти" : "Зарегистрироваться"
    }

    private var passwordVisibilityTitle: String {
        showsPassword ? "Скрыть пароль" : "Показать пароль"
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading) {
                Text(title)
                    .font(.largeTitle)
                    .accessibilityAddTraits(.isHeader)
                    .accessibilityFocused($isHeadingAccessibilityFocused)

                Text("Почта")
                    .font(.headline)

                Text(confirmedEmail)
                    .textSelection(.enabled)
                    .accessibilityLabel("Почта")
                    .accessibilityValue(confirmedEmail)
                    .accessibilityIdentifier("auth.confirmed-email")

                Text("Пароль")
                    .font(.headline)

                passwordField

                Button(passwordVisibilityTitle, action: onTogglePasswordVisibility)
                    .buttonStyle(.bordered)
                    .accessibilityLabel(passwordVisibilityTitle)
                    .accessibilityValue(showsPassword ? "Показан" : "Скрыт")
                    .accessibilityIdentifier("auth.password-visibility")

                FeedbackView(feedback: feedback, onRetry: onRetry)

                Button(primaryActionTitle, action: onSubmit)
                    .buttonStyle(.borderedProminent)
                    .tint(.accentColor)
                    .controlSize(.large)
                    .frame(maxWidth: .infinity)
                    .disabled(isLoading || isSubmissionBlocked)
                    .accessibilityLabel(primaryActionTitle)
                    .accessibilityIdentifier("auth.submit-password")
            }
            .padding()
        }
        .scrollDismissesKeyboard(.interactively)
        .navigationTitle(title)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                navigationBackControl
            }
        }
        .task {
            isPasswordFocused = true
            isHeadingAccessibilityFocused = true
        }
    }

    @ViewBuilder
    private var passwordField: some View {
        if showsPassword {
            TextField("Пароль", text: $password)
                .textContentType(.password)
                .submitLabel(.go)
                .focused($isPasswordFocused)
                .accessibilityLabel("Пароль")
                .accessibilityIdentifier("auth.password")
                .onSubmit(onSubmit)
        } else {
            SecureField("Пароль", text: $password)
                .textContentType(.password)
                .submitLabel(.go)
                .focused($isPasswordFocused)
                .accessibilityLabel("Пароль")
                .accessibilityIdentifier("auth.password")
                .onSubmit(onSubmit)
        }
    }

    @ViewBuilder
    private var navigationBackControl: some View {
        if #available(iOS 26.0, *) {
            Button("Вернуться к почте", action: onBack)
                .buttonStyle(.glass)
                .accessibilityLabel("Вернуться к почте")
                .accessibilityIdentifier("auth.back-to-email")
        } else {
            Button("Вернуться к почте", action: onBack)
                .buttonStyle(.bordered)
                .accessibilityLabel("Вернуться к почте")
                .accessibilityIdentifier("auth.back-to-email")
        }
    }
}
#endif
