# Mobile system design

Общий, platform-neutral baseline для крупных implementation changes. Он отвечает
за путь от landscape до plan; конкретные SDK и архитектура находятся в platform
layer.

| Тема | Файл |
|---|---|
| контекст, сущности, primary/secondary | [`system-design/landscape.md`](system-design/landscape.md) |
| holistic sequence и UI principles | [`system-design/hdd-ui-principles.md`](system-design/hdd-ui-principles.md) |
| mobile challenges | [`system-design/mobile-challenges.md`](system-design/mobile-challenges.md) |
| hard-to-reverse design gates | [`system-design/design-gates.md`](system-design/design-gates.md) |
| tasks и estimation | [`system-design/estimation-rfc.md`](system-design/estimation-rfc.md) |
| applicability/review | [`system-design/review.md`](system-design/review.md) |

Extended tier читает все файлы. Standard выбирает применимые темы. Quick всегда
делает хотя бы landscape и secondary-requirements check.
