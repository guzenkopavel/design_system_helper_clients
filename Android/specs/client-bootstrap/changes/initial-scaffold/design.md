# Design — client bootstrap / Android / initial scaffold

Design status: NOT_APPLICABLE: This quick change records a tool-generated shell and deliberately defers product architecture decisions to feature work.

## Applied engineering scopes

- application: The generated activity is retained only as the initial application boundary and composition entry point.
- compose: The generated composable provides a minimal state-free rendering baseline without defining reusable product UI.
- gradle: Wrapper, version catalog, settings, and module scripts form the discovered reproducible build boundary.
- ui: Theme and resources remain template assets whose accessibility and design-system behavior is not yet product-approved.
