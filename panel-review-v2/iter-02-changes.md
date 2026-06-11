# Iter-02 changes (builder log)

Responding to iter-01 feedback. All six blockers and all five majors addressed; minors A6, A7, A8, A9, J6, J7, J8 also done.

## Blockers

**A1 — preview now renders the headline.**
The opened-email mock's heading slot is now `#prev-headline-email`, fed from the "Article headline" field. The subject line no longer impersonates the email heading.

**A2 — send button reachable at all widths.**
The `<900px` media query no longer hides `#preview-panel`; it stacks it full-width under the form (`#compose-view` flips to column, body becomes scrollable). Nothing is amputated.

**A3 — audit page role chip tells the truth.**
`/audit` accepts `?role=` (validated against the same whitelist as `/`), renders the chip text + colour for the actual role. The compose page's audit-nav link and the audit page's back/compose links all carry the role through. Bad values fall back to `sender`.

**J1 — in-flight send lock.**
`sendAlert()` sets `state.sending`, disables the button and repaints it as "Sending…"/"Scheduling…" before the fetch. Second clicks are no-ops; `updateSendButton()` won't repaint mid-request.

**J2 — two-step confirm on the send button.**
First click arms: button turns Guardian-red, reads "Confirm: send to N segments" (or "Confirm: schedule for HH:MM" / "🎓 Confirm practice send"), hint names the segments, an explicit "Cancel — don't send" link appears. Second click sends. Auto-disarms after 8s, on Esc, on the cancel link, or on any form change. Trainees get the same gesture — practising the real flow is the point.

**J3 — past schedules rejected on both sides.**
Client: date input gets `min=today`, `updateSendButton()` checks the chosen local datetime is in the future and explains otherwise ("Scheduled time is in the past — pick a future time"). Server: `/api/send` parses `sched_at`, 400s on malformed input and on times more than 60s in the past. Verified by API test.

## Majors

**A4 — inbox preview stripe.** Preview panel now shows "Inbox preview" (sender, "now", subject bold + preheader grey on one ellipsised line, Gmail-style) above "Opened email" (headline, image, body, CTA). The preheader no longer appears inside the email body.

**A5 — drafts survive role changes.** `onRoleChange()` snapshots every field + segments + timing into `sessionStorage`; `init()` restores and clears the snapshot after the reload (one-shot).

**J4 — missing-URL warning.** When the form is otherwise ready but URL is empty, the send hint warns: "⚠ No article URL — the 'Read more' link will go nowhere." (Non-blocking, as requested.)

**J5 — local timestamps.** Audit "Time" and "Scheduled time" cells carry `data-utc` and are formatted client-side to local "11 Jun 2026, 09:56". Cancel-confirm uses the same formatting and says "(your local time)".

**J6 — trainee schedule copy.** Practice-schedule banner now reads "nothing was delivered or scheduled."

## Minors

- **A6** — role chip has a visible ▾ caret.
- **A7** — preview image gets `onerror`/`onload` handlers; broken URLs hide the image and show "⚠ Image failed to load — check the image URL".
- **A8** — nav icons have `aria-label`s; the inert active-page "button" is now a `<span>` with `aria-current="page"` (both pages).
- **A9** — all `alert()`s on the compose page replaced with the banner in a red error variant (`showBanner(kind, title, sub)` helper; icons ❌/🧪/🎓/✅ per kind). Test button also disables while a test is in flight.
- **J7** — audit log has kind-pill toggles (All / Sent / Scheduled / Test / Trainee practice / Cancelled) that combine with the substring filter.
- **J8** — segments are recorded in every audit entry (send, scheduled, test) and shown in a new Segments column.

## Verification
- API smoke test: past/malformed schedule → 400; future schedule + sends OK; trainee dry-run OK; audit renders role chip, `data-utc`, pills, segments. All pass.
- Inline JS on both pages extracted and `node --check`ed — parses clean.
- Every `getElementById` target verified present in the rendered DOM on both pages.
- No headless browser available in this environment (download blocked), so visual checks were reasoned from markup/CSS rather than screenshots.
