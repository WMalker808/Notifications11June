# Iter-03 changes (builder log)

Responding to iter-02 feedback (3 must-fixes + 2 discretionary nits).

**A10 — duplicate check survives draft restore.**
`restoreDraft()` now re-runs `checkDuplicate(url)` whenever the restored draft has a URL, so the dup warning reappears after a role-change reload — including the trainee→sender promotion flow where it matters most. The URL status line also shows "✓ Draft restored" instead of sitting blank (covers Asha's second nit).

**J10 — missing-URL warning carried into the confirm prompt.**
`_armSend()` appends " — ⚠ no article URL" to the armed hint in all three variants (immediate / scheduled / trainee practice). The warning is now visible at the exact moment of commitment.

**A11 — aria-live announcements.**
`#send-hint` gets `aria-live="polite"`; the banner gets `role="status" aria-live="polite"`. Screen-reader users now hear the confirm prompt when the button arms, and the outcome banner when a send completes or fails.

**Nit — kind pills hidden on empty audit log.**
The pill row moved inside the `{% if audit_log %}` block; a fresh instance shows only "No activity yet."

## Verification
- Full API smoke suite re-run on a restarted instance: all pass (past/malformed schedule 400s, sends/practice OK, audit role chip + pills + segments + `data-utc` render).
- Rendered compose page asserts: `aria-live`, `role="status"`, "Draft restored", "no article URL" all present.
- Inline JS re-extracted and `node --check`ed — clean.
- Fresh-process audit page confirmed: zero `kind-pill` buttons rendered when the log is empty; "No activity yet" shows.
