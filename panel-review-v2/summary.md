# Panel review v2 — summary

## Outcome
**ACCEPT after 3 iterations** (limit was 10). Panel: **Asha** (UX usability expert, the Guardian) and **Jonah** (editorial tools designer, the Guardian).

Iter-01 reviewed the v1-accepted build and rejected it with 6 blockers; iter-02 fixed all blockers/majors but left 3 gaps; iter-03 closed them and was accepted.

## Iteration log
| Iter | Verdict | Headline issues |
|---|---|---|
| 01 | REJECT | Preview never rendered the headline field (showed subject instead); Send button vanished below 900px; double-click double-sent the broadcast; no confirm step on send-to-everyone; past schedule times accepted by client and server; audit page role chip hard-coded "Sender". |
| 02 | REJECT (narrow) | Blockers fixed; but dup-check lost on draft restore, no-URL warning swallowed by the confirm prompt, armed state silent for screen readers. |
| 03 | **ACCEPT** | All must-fixes verified. Only known-scope-cut polish remains. |

## What changed, by theme
- **Preview honesty** — opened-email mock now driven by the headline field; new Gmail-style inbox-preview stripe (subject bold + preheader grey); preheader removed from the email body mock; broken image URLs show an inline error instead of a broken-image icon.
- **Send safety** — two-step arm-then-confirm send button (red armed state naming segments, cancel link, Esc, 8s auto-disarm, disarm on any form change); in-flight lock kills the double-click double-send; missing-URL warning persists into the confirm prompt; past schedule times rejected client-side (min date + live hint) and server-side (400).
- **State truthfulness** — audit page role chip reflects the real role (role carried through all nav links); drafts survive role-change reloads via sessionStorage, including re-running the duplicate check; trainee practice-schedule copy now says "nothing was delivered or scheduled".
- **Audit usability** — local human-readable timestamps everywhere (table + cancel confirm); kind-pill filters combined with the text filter (hidden when log empty); segments recorded per entry and shown in a new column.
- **Layout & access** — <900px now stacks the preview panel under the form instead of hiding the only Send button; aria-labels on icon nav; aria-live on the send hint and outcome banner; role chip got a visible ▾; all compose-page `alert()`s replaced with an inline banner (success/test/practice/error variants).

## Deferred (known scope cuts, unchanged from v1)
Braze segment targeting, persistence across restarts, real Braze test-send, real Braze schedule cancellation, client-side role switching without reload, inline (non-`confirm()`) cancel flow on the audit page, per-client subject truncation indicator.

## Artefacts
- `iter-01-feedback.md` — panel review of the inherited build (REJECT, 6 blockers)
- `iter-02-changes.md` / `iter-02-feedback.md` — fixes + re-review (REJECT, 3 gaps)
- `iter-03-changes.md` / `iter-03-feedback.md` — fixes + re-review (**ACCEPT**)

## Verification methods
Running Flask instance; API smoke suite (CSRF-authenticated, all roles, both timing modes, past/malformed schedule rejection); rendered-DOM assertions on both pages; inline JS extracted and parsed with `node --check`; `getElementById` reference audit against rendered ids. No headless browser was available in the environment (download blocked by network policy), so visual layout was reviewed from markup/CSS rather than screenshots.
