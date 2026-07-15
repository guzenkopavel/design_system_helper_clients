//
//  SysDevScenApp.swift
//  SysDevScen
//
//  Created by pavel on 15.07.2026.
//

import SwiftUI
import CoreData

@main
struct SysDevScenApp: App {
    let persistenceController = PersistenceController.shared

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(\.managedObjectContext, persistenceController.container.viewContext)
        }
    }
}
