# Android package boundary guard

Read-only. Inspect discovered settings/Gradle graph, consumers and module
visibility; never assume names, tasks, plugins or variants. Feature/data/
network/storage/reusable UI capabilities use a Gradle Android library module or
Gradle Kotlin library module by strong default. The application module keeps
the exact app-shell allowlist, composition only and capability ownership `none`.

Exact output:

- `Verdict: PASS | BLOCK`
- `Outcome: isolated | deviation | not-applicable`
- `Capability triggers: independent-feature=yes|no; domain-data=yes|no; network=yes|no; persistence=yes|no; reusable-ui=yes|no; consumers=<integer>; independent-ownership=yes|no`
- `Isolation scope: module`
- `Physical unit: Gradle Android library module | Gradle Kotlin library module | none`
- `Repository evidence: <exact inspected settings/build paths>`
- `Public contract and dependency direction: <minimal seam/consumers>`
- `App-shell responsibilities: entry-points, lifecycle, root-routing, dependency-wiring, platform-configuration, target-resources`
- `App-shell capability ownership: none | BLOCK`
- `Deviation or N/A validation: <constraint/migration trigger or granularity evidence>`
- `Blockers: None | <exact blockers>`

Folder/package names are not modules. Deviation разрешён только в
existing/discovered library unit и никогда в application module. Missing fields, invalid deviation,
cycles/source leakage or feature/data/network implementation in the app module
returns `BLOCK`. Never edit files; architecture-designer records the verdict.
