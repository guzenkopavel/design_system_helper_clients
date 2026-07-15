# MVVM

View рендерит один State и отправляет typed Actions. ViewModel координирует Use
Cases, mapping и route contract, но не содержит business/data logic. Navigation
принадлежит Coordinator/Router. State updates происходят на MainActor; повторные
requests имеют explicit latest-wins/cancellation policy.

Checklist: один source of truth; DTO не протекает; loading/content/empty/error;
typed actions; testable transitions; navigation boundary; accessibility state.
