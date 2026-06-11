# Panel review v2 — iter-01 feedback

**Build under review:** the v1-accepted build (commit `b7bd663`), running locally, smoke-tested via API and full code walkthrough of `templates/index.html`, `templates/audit.html`, `app.py`.

**Panel:**
- **Asha** — senior UX / usability expert, the Guardian. Heuristic evaluation + "3am stressed journalist" walkthrough.
- **Jonah** — editorial tools designer, the Guardian. Designs internal newsroom tools; cares about error prevention, operational safety, and state consistency.

**Acceptance questions:**
1. Could a stressed journalist send a correct breaking-news email in under 60 seconds, without sending anything by accident?
2. Does every piece of state the UI shows tell the truth?

## Verdict: REJECT — 6 blockers

---

## Asha (UX usability expert)

**Q1: NO. Q2: NO.**

### Blockers

**A1. The preview lies — the "Article headline" field is never previewed.**
`updatePreview()` (index.html ~line 1030) reads subject, preheader, body and image — never `#headline`. The preview's heading slot (`#prev-subject-email`) renders the *subject line*, but the payload sent to Braze uses `headline` as the email's heading. So the one thing the preview exists to do — show what subscribers will receive — it gets wrong. Type a headline: nothing in the preview changes. Worse, a journalist who notices the preview heading is wrong will "fix" the subject line instead of the headline. This is a trust-destroying defect in a preview-led tool.

**A2. Below 900px the Send button ceases to exist.**
`@media (max-width: 900px) { #preview-panel { display: none; } }` — and `#send-btn` lives inside `#preview-panel`. On a split-screen laptop (very common in the newsroom: tool on one half, live blog on the other) the only send button in the application is gone, with no fallback. Combined with `body { overflow: hidden; height: 100vh }`, nothing reflows — the tool is simply unusable. Stack the panels instead of amputating one.

**A3. The audit page role chip is hard-coded to "Sender".**
Switch to Trainee on compose, click the Audit icon: the sidebar chip says "Sender" (audit.html line 249 is literal text). A trainee now believes they're in Sender mode; the next thing they do is navigate back and — depending on how they navigate — possibly land on `/` which defaults to `role=sender`. A safety feature that misreports itself is worse than no feature. Role must be carried through navigation and rendered truthfully on every page.

### Majors

**A4. Preheader is previewed in the wrong place, and there is no inbox preview.**
The preview renders the preheader as an italic line *inside the opened email body*. Preheaders don't appear there — they appear next to the subject in the inbox list. The v1 panel already asked for an "inbox preview" stripe (subject bold + preheader grey, Gmail-style). With A1, the right structure is: inbox stripe (subject + preheader) above the opened-email mock (headline, image, body, CTA). That makes all four fields self-explanatory at a glance.

**A5. Changing role throws away the draft.**
`onRoleChange()` does a full page reload. A trainee who drafts a practice send, then switches to Sender to send it for real (the *intended* workflow), loses everything. Carried from v1 as a nit; in a role-based workflow it's a major. Persist the draft (sessionStorage) across the reload — no backend change needed.

### Minors

- **A6.** Role chip still has no visible ▾ — the invisible `<select>` overlay gives zero affordance (v1 nit, still open).
- **A7.** Broken image URL paste → raw broken-image icon in the preview; add `onerror` handling.
- **A8.** Icon-only nav buttons (✏️, 📋) have tooltips but no `aria-label`; the active "Compose" control is a `<button>` that does nothing.
- **A9.** Errors surface as `alert()` dialogs — modal, jarring, and they steal focus mid-crisis. Use the existing banner pattern in an error colour.

---

## Jonah (editorial tools designer)

**Q1: NO. Q2: NO.**

### Blockers

**J1. Double-click → double broadcast.**
`sendAlert()` guards on `disabled`/`sent` classes, but the button is not disabled while the request is in flight — it stays `ready` until the response arrives. A double-click (or an anxious second click on a slow connection, i.e. exactly the 3am scenario) fires `/api/send` twice and emails every subscriber twice. Disable the button and show "Sending…" the moment the first click lands.

**J2. One click broadcasts to everyone — no confirmation.**
"⚡ Send Newsletter" goes straight to every selected segment. The *test* send is one click and so is the *real* send; the only difference is which button you reached for. Every comparable newsroom tool has a final gate. Wants a lightweight arm-then-confirm on the button itself (not a modal — speed matters): first click arms it ("Confirm: send to 2 segments"), second click sends, auto-disarm after a few seconds or on cancel. Trainee should get the same flow — practising the real gesture is the point of trainee mode.

**J3. You can schedule a send in the past.**
Verified live: `sched_at: "2020-01-01T10:00:00"` → `{"success": true}`. No client-side check, no server-side check. Against real Braze this is an API error at best and an instant accidental send at worst. Client: validate future-ness, set `min` on the date input, say why the button is disabled. Server: reject past times — the client check alone isn't enough because the server is the audit-keeper.

### Majors

**J4. Send is enabled with no article URL.**
Required-to-send is subject + segment only. The email's "Read more →" CTA then points nowhere. Don't hard-block (there are conceivable no-link sends) but the send hint must warn loudly when URL is empty, and the confirm step (J2) should restate it.

**J5. Raw UTC ISO timestamps everywhere a human reads time.**
Audit table "Time" column, "Scheduled time" column, and the cancel-confirm dialog all show `2026-06-11T08:56:36Z`. The journalists this is for live in BST. Format to local, human-readable, everywhere (v1 nit, still open).

**J6. Trainee "practice schedule" success copy is misleading.**
Banner says "nothing was delivered to subscribers" — true, but the trainee just clicked "Practice schedule" and will go to /audit expecting a pending schedule. Say "nothing was delivered or scheduled" (v1 nit, one-line fix, still open).

### Minors

- **J7.** Audit filter is substring-only; "show me only real sends" requires typing "send" which also matches "scheduled". Kind-pill toggles above the table (v1 nit, still open).
- **J8.** Segments are collected in the payload but `app.py` ignores them — neither stored in the audit entry nor sent to Braze. For the prototype, at minimum record them in the audit log so the log answers "who was this sent to?".
- **J9.** `confirm()`/`alert()` on the audit cancel flow — acceptable for now, consistent with A9 longer-term.

---

## Carried-over v1 nits adopted into this review
Role-chip chevron (A6), inbox preview (A4), draft loss on role change (A5), raw ISO in cancel-confirm (J5), kind-pill audit filter (J7).

## Required for ACCEPT
Fix all six blockers (A1, A2, A3, J1, J2, J3) and the majors (A4, A5, J4, J5, J6). Minors at builder's discretion but A6/J6-class one-liners are expected.
