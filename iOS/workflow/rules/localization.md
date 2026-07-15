# iOS localization

User-visible strings must use the localization mechanism already present in the
client; discover keys, tables and generation tools before editing. Avoid string
concatenation that prevents grammatical reordering. Verification covers missing
keys, interpolation/plural forms, expanded text layout and at least one
non-default locale when localization is in task scope.
