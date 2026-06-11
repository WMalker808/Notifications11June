# Iteration 02 — Builder changes

Addresses all 6 priority items plus the bundled nits from iter-01 feedback.

## `app.py`

- `/api/send`: replaced `role != "sender"` gate with explicit `role == "viewer"` block (returns 403). Trainee is now permitted through.
- New `is_trainee` branch: when role is `trainee`, Braze is **never** called (regardless of `BRAZE_API_KEY`). The audit entry is written with `kind="trainee_practice"`. For scheduled trainee practice, the row is NOT added to `SCHEDULED_SENDS` (so it can't be cancelled from the pending list, since nothing is actually scheduled with Braze).
- `/api/send` now returns `{"success": True, "trainee_practice": <bool>}` so the client can pick the right banner.
- `/api/send-test`: same change — `viewer` blocked, `trainee` allowed. Trainee test-sends are still logged with `kind="test"` per the spec.

## `templates/index.html`

### Field order + helper text
- Content card field order is now: URL → subject → preheader → headline → body → image. Image URL block moved to the end of the card.
- Added `.field-hint` muted helper line under three labels:
  - Subject line: "Shown in the recipient's inbox subject line."
  - Preheader: "Shown next to the subject in the inbox preview line."
  - Article headline: "Displayed inside the email body as the main heading."
- New `.field-hint` style: 12px, `var(--ink-500)`, 2px top margin, non-uppercase.

### Image: "Use article image" ghost button
- Image URL row now wraps the input + a "Use article image" ghost button (`.ghost-btn` style).
- Button is disabled by default and only enabled once `fetchArticle()` returns an `og:image`.
- New `state.articleImageUrl` stores the fetched value; `useArticleImage()` restores it.

### Send vs Send-test separation (high priority)
- Removed `#send-test-btn` and the `.test-row` block from the right rail.
- Added a new "Test before sending" mini-card (`.test-card`) at the bottom of the form panel, after the Delivery & Timing card. Dashed border (`1.5px dashed var(--ink-400)`), ghost-styled `#send-test-btn-card` button labelled "🧪 Send test email", with the recipient input inline.
- Right rail now contains only the primary Send button — clear visual separation between practice (mid-form, dashed, ghost) and real send (right rail, navy, primary).
- Success banner adds `kind-test` or `kind-practice` modifier classes that paint it amber (`#fcf3de` background, `var(--warn)` accent) — visually distinct from the green "real send" banner.

### Trainee role does something useful
- `updateSendButton()`: distinguishes `viewer` (always disabled, "Read-only role — switch to Sender to send.") from `trainee` (button enabled, label "🎓 Practice send" / "🎓 Practice schedule", hint "Trainee mode — sends are recorded but not delivered.").
- After a successful trainee submit: amber banner reads "Practice send recorded (Braze not called)" with sub "Trainee mode — nothing was delivered to subscribers." Send button flips to "✓ Practice recorded".
- Audit page renders these rows with the `chip-amber` "Trainee practice" chip.

### Segment-required gate (real bug)
- `updateSendButton()` no longer has `const hasSegment = true;`. Now uses `Object.values(state.segments).some(Boolean)`. Hint string when blocked is "Select at least one segment to send." Both the main button and the test button respect this for the send flow (test button stays gated only by subject + non-viewer role, per the spec — testing without a segment is legitimate).

### Braze copy toned down (user-facing)
- Channel card: "Email via Braze" → "Email". Channel badge "Braze" → "Email".
- Routing detail: "Immediate send via Braze" → "Immediate send". Scheduled equivalent updated. Routing badge "Braze" → "Email".
- Timing button copy: "Send right now via Braze" → "Send right now".
- Success default sub: "Sent via Braze" → empty.
- `TIMING_DETAILS` constant updated accordingly.
- The only remaining "Braze" string in `index.html` is the spec-mandated "Practice send recorded (Braze not called)" trainee banner, plus an internal JS code comment and the legacy `.route-braze` CSS class name (not user-visible).

### Role chip styling
- Sidebar role picker now rendered as a coloured pill (`.role-chip`) with the role label visible. The `<select>` is still functional — absolutely positioned over the chip with `opacity: 0`, preserving native dropdown behaviour. Chip colour shifts by role: sender (blue), trainee (amber/warn), viewer (gray). A small "Role" caption sits above it.
- Removed the old `.role-picker-wrap` / `#role-picker` rules.

### Dup-warn copy
- `checkDuplicate()` now computes same-day vs prior-day from the parsed timestamp and the current time. Output is now `"earlier today at HH:MM"` or `"yesterday at HH:MM"` (instead of always "today").

## `templates/audit.html`

- Added the 60px navy sidebar (same logo, nav buttons, role chip layout as `index.html`). Compose nav links back to `/`. Static "Sender" role chip — audit page doesn't need a live role selector.
- New text filter (`#activity-filter`) above the activity table — single substring filter, case-insensitive, matches against the row's full textContent (covers URL, subject, role, kind, timing, status, time). Shows an empty-state line when nothing matches.
- `cancelScheduled(id, btn)`: confirm prompt now reads `Cancel the scheduled send "<headline>"?  Scheduled for <sched_at>.` Headline + time pulled from data-attributes on the button.
- Kind chip mapping now includes `trainee_practice → chip-amber` and renders the human label "Trainee practice" instead of the raw key.

## Open / out-of-scope (per spec)

- Real Braze cancellation API call.
- Delivery confirmation banner on the compose page (the audit log already shows status).
- Persistence across server restarts (`AUDIT_LOG`, `SCHEDULED_SENDS` remain in-process).
- Audit-page search beyond simple substring.
