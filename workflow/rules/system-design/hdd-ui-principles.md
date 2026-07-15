# Holistic-driven design

Предпочтительная последовательность: domain contracts → service/repository stubs
→ UI на детерминированных stubs → real integrations → cache/offline → tests →
secondary behavior → guarded rollout. Отклонение требует зависимости и причины.

Для UI проверить: один state owner, явные actions, loading/error/empty/content,
predictable navigation/back, сохранение контекста, interruption recovery,
feedback для действий, accessibility, localization, design-system primitives,
адаптацию размеров и отсутствие скрытых destructive defaults.
