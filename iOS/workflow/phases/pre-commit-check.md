# iOS addendum: Pre-commit Check

Swift/Xcode/SPM/SwiftLint checks применяются только при обнаруженных
project/package/config/tool inputs. Project, scheme, target, destination и new
Swift target membership не придумываются. Localization/accessibility/UI требуют
task evidence и simulator/runtime evidence только для соответствующих paths.
Greenfield отсутствие проекта/tooling даёт N/A или risk-based UNKNOWN.
