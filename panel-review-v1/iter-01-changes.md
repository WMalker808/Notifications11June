# Iteration 01 — Builder changes

## `app.py`
- Removed intelligent timing branch from `/api/send`. `_braze_schedule(...)` still carries the `at_optimal_time` param (defaults False) but no caller passes True.
- `_braze_send` and `_braze_schedule` now take `(headline, subject, preheader, body, url, image_url=None)`. Hardcoded `"Breaking news: " + headline` removed — subject comes from caller. `preheader` passed through `trigger_properties.preheader`.
- New `_add_utm(url)` helper appends `utm_source=newsletter&utm_medium=email&utm_campaign=breaking-news` idempotently (skips if `utm_source=` is already present). Wired into both Braze functions on the outgoing `url` field. Companion `_strip_utm` used for duplicate comparison.
- Added module-level in-memory stores: `AUDIT_LOG` (newest first, capped on read at 200) and `SCHEDULED_SENDS` (id → entry).
- `/api/send` now accepts `subject`, `preheader`, `image_url`, `role`. Generates `uuid4()` for scheduled sends, pushes to `SCHEDULED_SENDS` + `AUDIT_LOG`. Immediate sends push to `AUDIT_LOG` only. Each audit entry has `{id, ts, role, kind, timing, headline, subject, preheader, url, status:"ok"}`.
- `POST /api/send-test` — dev-mode mock; logs to `AUDIT_LOG` with `kind="test"` and `test_recipient`. Real Braze test sending is left as a TODO comment.
- `GET /audit` renders `audit.html` with `audit_log=AUDIT_LOG[:200]` and `scheduled=list(SCHEDULED_SENDS.values())`.
- `POST /api/cancel-scheduled` removes from `SCHEDULED_SENDS`, adds a `kind="cancel"` audit entry. Returns 404 if id not found.
- `POST /api/check-duplicate` searches `AUDIT_LOG` for `kind in ("send","scheduled")` with same URL (UTM-stripped) within the last 6 hours; returns `{duplicate, last_sent_at}`.
- Role gating in `/api/send` and `/api/send-test`: non-`sender` roles get a 403. Validated against `_VALID_ROLES = ("sender","trainee","viewer")`.
- `GET /` reads `?role=` param, validates, passes to template.
- All new endpoints call `_require_csrf()`.

## `templates/index.html`
- Sidebar avatar "M" replaced by a `<select id="role-picker">` (Sender / Trainee / Viewer) and a sidebar nav button linking to `/audit`. Role change reloads with `?role=` in the URL.
- Content card: inserted three new fields between URL and the (renamed) headline field:
  - `#subject` (default `"Breaking news: "`, counter to 200, warns at 180).
  - `#preheader` (maxlength 100, counter warns at 90).
  - `#image-url` (pre-filled from `og:image` via `fetchArticle`).
- The old `#headline` is kept but relabelled "Article headline" — it now drives only the preview body / Braze `headline` property, not the subject. Its maxlength bumped to 200 since it's no longer the subject.
- Duplicate-URL warning banner `#dup-warn` (hidden by default, shown above content card) reads "This URL was already sent at HH:MM today — proceed with caution."
- Delivery & Timing card: deleted intelligent-timing button and the full `#intelligent-panel` callout. Grid is now 2-column. Removed dead CSS for `.timing-btn.selected-intelligent`, `#intelligent-panel`, and `.it-*` helpers.
- Email preview: now renders subject (no `Breaking news:` prefix added — the field already contains it), preheader as small italic muted line, optional image via `#image-url`, and body.
- Test-send: small `#test-recipient` input (default `test@theguardian.com`) and `#send-test-btn` placed above/below the main send button.
- JS:
  - `state` extended with `role` and `sendingTest`.
  - New `onRoleChange()` re-navigates with `?role=`.
  - `fetchArticle()` now also populates `image-url`, sets subject only if user hasn't customised it past `"Breaking news: "`, then calls `checkDuplicate()`.
  - `selectTiming` no longer references `intelligent`. `TIMING_DETAILS` reduced to `immediate` + `scheduled`.
  - `updateSendButton()` disables both buttons when `state.role !== 'sender'` and shows "Read-only role — switch to Sender to send."
  - `sendAlert()` payload now includes `subject`, `preheader`, `image_url`, `role`. All intelligent branches removed.
  - New `sendTest()` posts to `/api/send-test` and shows a different success banner.

## `templates/audit.html` (NEW)
- Back-link to `/`.
- Section 1: pending scheduled sends table (Headline / Scheduled time / Cancel button), empty state copy "No pending scheduled sends."
- Section 2: recent activity table (Time / Role / Kind / Timing / Subject / URL / Status). `Kind` rendered as a `.chip` with `chip-blue` (send), `chip-amber` (scheduled), `chip-gray` (test), `chip-red` (cancel). Status uses `chip-green`. Empty state "No activity yet."
- Vanilla JS cancel button posts CSRF-protected `/api/cancel-scheduled` then reloads.

## `static/guardian.css`
- Untouched. Existing `.chip` classes (chip-blue / amber / green / gray / red) and `.input` / `.textarea` / shadow / radius tokens were sufficient.

## Open questions / TODOs
- Real Braze test-send is mocked. The Braze "Send Test" REST endpoint differs from broadcast trigger and needs a real `campaign_id` + `external_user_id` design — flagged in `send_test()` as TODO.
- AUDIT_LOG / SCHEDULED_SENDS are in-process only. Anything restart-persistent (Redis / SQLite) is out of scope for this iteration.
- `_braze_schedule` keeps `at_optimal_time` param for now but no caller uses it. Safe to drop in a future iteration if confirmed.
- Role gating is enforced both client-side (button disable) and server-side (403). Trainee role currently behaves identically to Viewer — distinction is purely cosmetic in the picker label. Panel may want a real Trainee mode (e.g. dry-run with audit but no Braze call) — flag for tester.
- The duplicate-check uses 6-hour window per spec. May want this configurable later.
- The role picker reload causes a flash; could be done client-side without a reload, but reload keeps server-rendered `{{ role }}` source-of-truth.
