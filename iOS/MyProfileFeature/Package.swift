// swift-tools-version: 6.3

import PackageDescription

let package = Package(
    name: "MyProfileFeature",
    platforms: [
        .iOS("18.0"),
        .macOS("13.0")
    ],
    products: [
        .library(
            name: "MyProfileFeature",
            targets: ["MyProfileFeature"]
        )
    ],
    dependencies: [
        .package(path: "../AuthFeature")
    ],
    targets: [
        .target(
            name: "MyProfileFeature",
            dependencies: ["AuthFeature"],
            swiftSettings: [
                .enableUpcomingFeature("StrictConcurrency")
            ]
        ),
        .testTarget(
            name: "MyProfileFeatureTests",
            dependencies: ["MyProfileFeature"],
            swiftSettings: [
                .enableUpcomingFeature("StrictConcurrency")
            ]
        )
    ]
)
