# Design — <feature> / <platform> / <change-id>

<!-- Все архитектурные объяснения и решения писать по-русски; exact schema,
идентификаторы, пути, код и названия API сохранять без перевода. -->

## Current context
## Proposed architecture and boundaries
## Data and control flow
## Dependency injection
## Error and recovery model
## Concurrency model
## Security and data handling
## Platform SDK considerations
## Design-system and accessibility
## Migration and rollout
## Alternatives and trade-offs

Следующий раздел должен содержать только точные структурированные строки. Две
канонические app-shell строки — единственные shell claims; остальные поля не
могут ссылаться на `app`, `application`, `shell`, `target` или `module` в любом
порядке либо possessive form. Формулировка physical unit использует точную
разрешённую адаптером non-application phrase.

## Modularity decision

- Outcome: isolated | deviation | not-applicable
- Capability triggers: independent-feature=yes|no; domain-data=yes|no; network=yes|no; persistence=yes|no; reusable-ui=yes|no; consumers=<integer>; independent-ownership=yes|no
- Physical boundaries: <existing/discovered/proposed non-application adapter physical unit; N/A local boundary>
- Public contracts and dependency direction: <minimal API, consumers and acyclic direction>
- App-shell responsibilities: entry-points, lifecycle, root-routing, dependency-wiring, platform-configuration, target-resources
- App-shell capability ownership: none
- Repository evidence: <existing-repo-path>[; <existing-repo-path>]
- Rationale and trade-offs: <why this outcome fits the evidence>
- Migration boundary and trigger: <typed seam and objective trigger, or evidence-backed N/A>
- Over-modularization check: <why granularity is neither per-folder/layer nor monolithic>
- Boundary guard verdict: PASS | BLOCK

## Applied engineering scopes

- <scope>: <decision or explicit N/A with rationale>

## Platform UX trace and decisions

Для product-backed `ui` сослаться на `platform-ux.md` и по-русски объяснить, как
его native language, appearance, accessibility/motion и fallback decisions
влияют на архитектуру без копирования shared UX.

## System-design checklist
## Verification strategy
