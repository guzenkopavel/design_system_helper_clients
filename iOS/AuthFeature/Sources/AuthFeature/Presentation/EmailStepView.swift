#if os(iOS)
import SwiftUI

struct EmailStepView: View {

    @Binding var email: String

    let feedback: AuthFlowState.Feedback
    let isLoading: Bool
    let isSubmissionBlocked: Bool
    let onSubmit: () -> Void
    let onRetry: () -> Void

    @FocusState private var isEmailFocused: Bool
    @AccessibilityFocusState private var isEmailAccessibilityFocused: Bool

    var body: some View {
        ScrollView {
            VStack(alignment: .leading) {
                Text("Авторизация")
                    .font(.largeTitle)
                    .accessibilityAddTraits(.isHeader)

                Text("Введите адрес электронной почты, чтобы продолжить.")
                    .foregroundStyle(.secondary)

                Text("Почта")
                    .font(.headline)

                TextField("Почта", text: $email)
                    .textFieldStyle(.roundedBorder)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .keyboardType(.emailAddress)
                    .textContentType(.emailAddress)
                    .submitLabel(.continue)
                    .focused($isEmailFocused)
                    .accessibilityFocused($isEmailAccessibilityFocused)
                    .accessibilityLabel("Почта")
                    .accessibilityIdentifier("auth.email")
                    .onSubmit(onSubmit)

                FeedbackView(feedback: feedback, onRetry: onRetry)

                Button("Продолжить", action: onSubmit)
                    .buttonStyle(.borderedProminent)
                    .tint(.accentColor)
                    .controlSize(.large)
                    .frame(maxWidth: .infinity)
                    .disabled(isLoading || isSubmissionBlocked)
                    .accessibilityLabel("Продолжить")
                    .accessibilityIdentifier("auth.continue")
            }
            .padding()
        }
        .scrollDismissesKeyboard(.interactively)
        .navigationTitle("Почта")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            isEmailFocused = true
            isEmailAccessibilityFocused = true
        }
    }
}
#endif
