# iOS addendum: Archive

Implementation archives use the adapter namespace
`iOS/specs/<feature>/archive/<YYYY-MM-DD-change-id>/`. Preflight must prove fresh
iOS verification and keep the shared product source unchanged. Apply leaves the
exact `changes/<change-id>/ARCHIVED.md` tombstone and never overwrites an
existing archive.
