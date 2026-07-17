import AuthFeature
import SwiftUI
#if os(iOS)
import UIKit
#endif

struct MyProfileView: View {

    private let state: MyProfileState
    private let onReload: @MainActor @Sendable () async -> Void
    private let onLogout: @MainActor @Sendable () async -> Void
    private let strings = MyProfileStrings.shared

    @State private var countMessage: String?
    @Environment(\.colorScheme) private var colorScheme
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @Environment(\.accessibilityReduceTransparency) private var reduceTransparency

    init(
        state: MyProfileState,
        onReload: @escaping @MainActor @Sendable () async -> Void = {},
        onLogout: @escaping @MainActor @Sendable () async -> Void = {}
    ) {
        self.state = state
        self.onReload = onReload
        self.onLogout = onLogout
    }

    var body: some View {
        let model = MyProfilePresentationModel.make(from: state, strings: strings)
        let visual = MyProfileVisualEnvironment(
            colorScheme: colorScheme,
            contrast: .normal,
            reduceMotion: reduceMotion,
            reduceTransparency: reduceTransparency
        )

        ScrollView {
            VStack(spacing: 24) {
                header(model: model, visual: visual)
                actionGroup(model: model, visual: visual)
                messageArea(model: model, visual: visual)
            }
            .frame(maxWidth: 520)
            .frame(maxWidth: .infinity)
            .padding(.horizontal, 24)
            .padding(.vertical, 32)
        }
        .background(contentBackground)
        .task {
            if case .idle = state {
                await onReload()
            }
        }
    }

    private func header(
        model: MyProfilePresentationModel,
        visual: MyProfileVisualEnvironment
    ) -> some View {
        VStack(spacing: 12) {
            Image(systemName: visual.profileSymbolName)
                .font(.system(size: 72, weight: .regular))
                .foregroundStyle(.blue)
                .accessibilityLabel(strings.profileSymbolLabel)
                .accessibilityIdentifier("my-profile.symbol")

            if let email = model.email {
                Text(email)
                    .font(.title3.weight(.semibold))
                    .multilineTextAlignment(.center)
                    .lineLimit(3)
                    .minimumScaleFactor(0.75)
                    .accessibilityLabel(strings.profileEmailLabel)
                    .accessibilityValue(email)
            } else if model.isLoading {
                ProgressView(strings.loading)
                    .controlSize(.regular)
            }
        }
        .padding(.top, 8)
    }

    private func actionGroup(
        model: MyProfilePresentationModel,
        visual: MyProfileVisualEnvironment
    ) -> some View {
        VStack(spacing: 12) {
            Button {
                countMessage = MyProfilePresentationModel.countFeedback(for: state, strings: strings)
            } label: {
                Label(strings.myInterviews, systemImage: "list.bullet.rectangle")
                    .frame(maxWidth: .infinity, minHeight: 44)
            }
            .buttonStyle(.borderedProminent)
            .tint(.blue)
            .disabled(!model.isMyInterviewsEnabled || model.isLogoutLoading)
            .accessibilityHint(model.myInterviewsAccessibilityHint)

            Button(role: .destructive) {
                Task { await onLogout() }
            } label: {
                Label(model.isLogoutLoading ? strings.logoutInProgress : strings.logout, systemImage: "rectangle.portrait.and.arrow.right")
                    .frame(maxWidth: .infinity, minHeight: 44)
            }
            .buttonStyle(.bordered)
            .disabled(model.isLogoutLoading)
            .accessibilityHint(model.isLogoutLoading ? strings.logoutInProgress : strings.logout)
        }
        .padding(16)
        .background(groupBackground(visual: visual), in: RoundedRectangle(cornerRadius: 8, style: .continuous))
    }

    @ViewBuilder
    private func messageArea(
        model: MyProfilePresentationModel,
        visual: MyProfileVisualEnvironment
    ) -> some View {
        if let message = countMessage ?? model.statusMessage {
            Text(message)
                .font(.callout)
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
                .padding(.horizontal, 16)
                .padding(.vertical, 10)
                .background(.thinMaterial, in: Capsule())
                .animation(visual.feedbackAnimation, value: message)
                .accessibilityAddTraits(.isStaticText)
                .accessibilityLabel(message)
        }
    }

    private func groupBackground(visual: MyProfileVisualEnvironment) -> some ShapeStyle {
        visual.usesTransparencyFallback ? AnyShapeStyle(fallbackGroupBackground) : AnyShapeStyle(.regularMaterial)
    }

    private var contentBackground: Color {
        #if os(iOS)
        Color(uiColor: .systemGroupedBackground)
        #else
        Color(nsColor: .windowBackgroundColor)
        #endif
    }

    private var fallbackGroupBackground: Color {
        #if os(iOS)
        Color(uiColor: .secondarySystemGroupedBackground)
        #else
        Color.secondary.opacity(0.08)
        #endif
    }
}

extension MyProfileFeatureFactory {

    @MainActor
    public func makeProfileView(
        sessionClient: any AuthSessionRequesting,
        onSignedOut: @escaping @MainActor @Sendable () async -> Void
    ) -> some View {
        MyProfileContainerView(
            store: makeStateStore(
                sessionClient: sessionClient,
                recoverInvalidSession: onSignedOut
            ),
            onSignedOut: onSignedOut
        )
    }
}

private struct MyProfileContainerView: View {
    let store: MyProfileStateStore
    let onSignedOut: @MainActor @Sendable () async -> Void

    @State private var profileState: MyProfileState

    init(
        store: MyProfileStateStore,
        onSignedOut: @escaping @MainActor @Sendable () async -> Void
    ) {
        self.store = store
        self.onSignedOut = onSignedOut
        _profileState = State(initialValue: store.state)
    }

    var body: some View {
        MyProfileView(
            state: profileState,
            onReload: reload,
            onLogout: logout
        )
    }

    private func reload() async {
        await store.reload()
        profileState = store.state
    }

    private func logout() async {
        await store.logout()
        profileState = store.state
        if case .signedOut = profileState {
            await onSignedOut()
        }
    }
}
