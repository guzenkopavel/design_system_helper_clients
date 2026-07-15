# Wording clarity

Platform artifacts должны читаться cold без чата и скрытого знания кода.

- Security/privacy `MUST` начинается с названной угрозы и затем control.
- Каждый AC описывает один observable outcome, не implementation state и не
  набор взаимоисключающих вариантов.
- Existing component/path при первом упоминании получает короткое объяснение;
  proposed greenfield path помечается как proposed.
- Positive и rejected cases разделяются структурно.
- Anti-pattern называет root cause, источник (`existing` или `industry`) и
  rationale отказа.
- Местоимение имеет однозначный близкий antecedent.
- Один контракт не копируется между proposal/spec/design/plan; downstream даёт
  ссылку и добавляет только собственный контекст.

Threatless security rule, non-observable AC и смешанный contradictory outcome —
blocker до `specified`. Остальное исправляется до planning либо фиксируется
явным non-blocking finding.
