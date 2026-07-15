# Networking performance

Оптимизация начинается с request waterfall, payload sizes, cache behavior,
connection reuse и server timing. Нельзя предполагать cache policy конкретной
session configuration — она читается из кода/configuration.

- Avoid duplicate requests через explicit identity и single-flight там, где
  семантика запросов одинакова.
- Cache имеет freshness, validation, privacy и offline contracts.
- Pagination/prefetch bounded и отменяется при потере owner.
- Retry учитывает idempotency, backoff, reachability semantics и server hints.
- Compression/decoding измеряются вместе с CPU/memory trade-off.
- URL construction использует structured components и корректное encoding.

Network condition контролируется или подробно записывается. Live endpoint
variance не превращается в deterministic PASS; при недоступной среде статус
UNKNOWN и сохраняются diagnostics.
