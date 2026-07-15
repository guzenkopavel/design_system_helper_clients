# Security review

Security mode сочетает bounded deterministic scan и contextual human review.
Scanner finding — сигнал, не verdict. Reviewer подтверждает достижимость,
trust boundary, data exposure и существующие controls; false positive
отклоняется с current-context evidence.

Обязательные lenses: secrets/redaction, least privilege, runtime hook command
construction, remote execution/exfiltration, prompt injection/untrusted
content, hidden Unicode, local absolute paths и optional MCP surface.

Никогда не выводить найденный secret/token/private-key fragment. Finding хранит
только severity/category/path/line/safe message. Safe placeholders, examples,
docs, scanner regex definitions и defensive detection prose не должны сами
создавать finding.

Недоступный scanner, unreadable surface или непройденная contextual validation
дают `UNKNOWN`. Нельзя писать `secure`, `fixed` или `verified` только по exit 0.
Scanner использует общий per-file/file-count/total-byte budget. Ошибка
enumeration/stat/read/UTF-8 decode, oversized declared text surface, budget
exhaustion или symlink escape оставляют safe coverage issue без content и дают
`UNKNOWN` с exit `3`; critical findings дают exit `2`, полный PASS — exit `0`.
Каждый declared text file читается bounded chunks из fd с `O_NOFOLLOW`, exact
lstat/fstat identity до и после чтения. Изменение identity/content budget или
candidate set между initial/final enumeration даёт coverage `UNKNOWN`.
