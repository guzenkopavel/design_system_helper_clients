// swift-tools-version: 6.3

import PackageDescription

let package = Package(
    name: "AuthFeature",
    platforms: [
        .iOS("18.0"),
        .macOS("13.0")
    ],
    products: [
        .library(
            name: "AuthFeature",
            targets: ["AuthFeature"]
        )
    ],
    targets: [
        .target(
            name: "AuthFeature",
            swiftSettings: [
                .enableUpcomingFeature("StrictConcurrency")
            ]
        ),
        .testTarget(
            name: "AuthFeatureTests",
            dependencies: ["AuthFeature"],
            resources: [
                .process("Fixtures")
            ]
        )
    ]
)
