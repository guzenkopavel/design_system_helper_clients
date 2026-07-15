# MVVM

View рендерит один State и отправляет typed Actions. ViewModel координирует Use
Cases, mapping и route contract, но не содержит business/data logic. Navigation
принадлежит Coordinator/Router. State updates происходят на MainActor; повторные
requests имеют explicit latest-wins/cancellation policy.

Checklist: один source of truth; DTO не протекает; loading/content/empty/error;
typed actions; testable transitions; navigation boundary; accessibility state.

ViewModel не должен становиться универсальным container: orchestration одной
feature допустима, reusable business rules уходят в Use Case. State желательно
делать value-semantic и наблюдаемым целиком; несколько независимых publishers
допустимы только при доказанной невозможности противоречивых комбинаций.

Effect policy задаёт, что происходит при повторном action: ignore, queue,
cancel-and-replace или parallel. Route output тестируется как typed event, а не
через знание concrete navigation controller. Preview/sample data не становится
runtime dependency.
