#if os(iOS)
import SwiftUI
import UIKit

/// Нативная поверхность двухшагового флоу авторизации.
public struct AuthFlowView: View {

    private let viewModel: AuthFlowViewModel

    @State private var state = AuthFlowState()
    @State private var email = ""
    @State private var password = ""
    @State private var synchronizationTask: Task<Void, Never>?

    public init(sessionModel: AuthSessionModel) {
        self.viewModel = sessionModel.makeAuthFlowViewModel()
    }

    public var body: some View {
        ZStack {
            NavigationStack {
                EmailStepView(
                    email: emailBinding,
                    feedback: state.feedback,
                    isLoading: state.phase == .loading,
                    isSubmissionBlocked: state.feedback.blocksPrimaryAction,
                    onSubmit: submitEmail,
                    onRetry: retry
                )
                .navigationDestination(isPresented: passwordStepPresented) {
                    if case .password(let confirmedEmail, let isLogin) = state.step {
                        PasswordStepView(
                            password: passwordBinding,
                            confirmedEmail: confirmedEmail,
                            isLogin: isLogin,
                            showsPassword: state.showPassword,
                            feedback: state.feedback,
                            isLoading: state.phase == .loading,
                            isSubmissionBlocked: state.feedback.blocksPrimaryAction,
                            onSubmit: submitPassword,
                            onRetry: retry,
                            onTogglePasswordVisibility: togglePasswordVisibility,
                            onBack: returnToEmail
                        )
                    }
                }
            }

            if state.phase == .loading {
                LoadingOverlay()
            }
        }
        .task {
            await refreshOnce()
        }
        .onDisappear {
            synchronizationTask?.cancel()
        }
    }

    private var emailBinding: Binding<String> {
        Binding(
            get: { email },
            set: { email = $0 }
        )
    }

    private var passwordBinding: Binding<String> {
        Binding(
            get: { password },
            set: { password = $0 }
        )
    }

    private var passwordStepPresented: Binding<Bool> {
        Binding(
            get: {
                if case .password = state.step {
                    return true
                }
                return false
            },
            set: { isPresented in
                guard !isPresented else { return }
                if case .password = state.step {
                    returnToEmail()
                }
            }
        )
    }

    private func submitEmail() {
        perform([.emailChanged(email), .submitEmail])
    }

    private func submitPassword() {
        perform([.passwordChanged(password), .submitPassword])
    }

    private func retry() {
        switch state.step {
        case .email:
            perform([.emailChanged(email), .retry])
        case .password:
            perform([.passwordChanged(password), .retry])
        }
    }

    private func togglePasswordVisibility() {
        perform([.toggleShowPassword])
    }

    private func returnToEmail() {
        password = ""
        perform([.backToEmail])
    }

    private func perform(_ actions: [AuthFlowAction]) {
        synchronizationTask?.cancel()
        synchronizationTask = Task {
            for action in actions {
                await viewModel.send(action)
            }
            await refreshUntilSettled()
        }
    }

    private func refreshUntilSettled() async {
        while !Task.isCancelled {
            let latestState = await viewModel.state
            apply(latestState)

            guard latestState.phase == .loading else { return }

            do {
                try await Task.sleep(for: .milliseconds(50))
            } catch {
                return
            }
        }
    }

    private func refreshOnce() async {
        apply(await viewModel.state)
    }

    private func apply(_ newState: AuthFlowState) {
        let previousState = state

        if previousState.phase != .loading,
           newState.phase == .loading,
           case .password = newState.step {
            password = ""
        }

        state = newState
        announceChanges(from: previousState, to: newState)
    }

    private func announceChanges(from previousState: AuthFlowState, to newState: AuthFlowState) {
        if previousState.step != newState.step {
            UIAccessibility.post(
                notification: .screenChanged,
                argument: newState.step.accessibilityHeading
            )
        }

        if previousState.phase != newState.phase {
            let message = newState.phase == .loading ? "Загрузка началась" : "Загрузка завершена"
            UIAccessibility.post(notification: .announcement, argument: message)
        }

        if previousState.feedback != newState.feedback,
           let message = newState.feedback.accessibilityAnnouncement {
            UIAccessibility.post(notification: .announcement, argument: message)
        }
    }
}

private extension AuthFlowState.Step {
    var accessibilityHeading: String {
        switch self {
        case .email:
            return "Почта"
        case .password(_, let isLogin):
            return isLogin ? "Вход" : "Регистрация"
        }
    }
}
#endif
