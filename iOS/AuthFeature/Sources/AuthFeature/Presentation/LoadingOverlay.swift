#if os(iOS)
import SwiftUI
import UIKit

struct LoadingOverlay: View {

    var body: some View {
        ZStack {
            Color(uiColor: .systemBackground)
                .ignoresSafeArea()

            ProgressView("Загрузка")
                .controlSize(.large)
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("Загрузка")
        .accessibilityAddTraits(.updatesFrequently)
        .accessibilityIdentifier("auth.loading")
    }
}
#endif
