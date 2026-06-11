# Dispatch — Newsletter Hub: Full Technical Documentation

## Overview

Dispatch is a single-page internal web tool for sending breaking news newsletters via the Braze customer engagement platform. A user pastes a Guardian article URL, the app fetches the headline and preview text automatically, the user customises subject/preheader/image and timing, and submits. The Flask backend then calls the Braze REST API to send or schedule the campaign.

The tool also exposes a separate `/audit` page that lists pending scheduled sends and recent activity, plus a mock role picker (Sender / Trainee / Viewer) so the workshop prototype can demonstrate access control and a trainee dry-run mode without real authentication.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask |
| Frontend | Vanilla HTML/CSS/JS (no framework) |
| Email delivery | Braze REST API |
| Deployment | Render (gunicorn WSGI server) |
| Dependencies | `flask`, `requests`, `python-dotenv`, `gunicorn` |

---

## Project Structure

```
dispatch/
├── app.py                  # Flask application — all backend logic
├── requirements.txt        # Python dependencies
├── render.yaml             # Render.com deployment config
├── .env                    # Environment variables (not committed)
├── static/
│   └── guardian.css        # Design token stylesheet
└── templates/
    └── index.html          # Single-page UI (HTML + embedded CSS + JS)
```

---

## Environment Variables

All secrets and configuration are loaded from a `.env` file via `python-dotenv`. The following variables are required:

| Variable | Description |
|---|---|
| `BRAZE_API_KEY` | Braze REST API key. Must have permissions for `campaigns.trigger.send` and `campaigns.trigger.schedule.create`. |
| `BRAZE_REST_ENDPOINT` | Base URL of the Braze REST endpoint (e.g. `https://rest.fra-01.braze.eu`). Defaults to the EU-01 endpoint if not set. |
| `BRAZE_CAMPAIGN_ID` | The ID of the Braze campaign to send. All sends — regardless of timing mode — go to this campaign and only this campaign. |
| `SECRET_KEY` | Flask session secret. If not set, a random key is generated at startup (sessions will not persist across restarts). |
| `PORT` | Port for the development server. Defaults to `5050`. |

---

## Backend (`app.py`)

### Application Startup

```python
load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
```

Environment variables are loaded and a Flask secret key is set for session management.

---

### CSRF Protection

All API endpoints call `_require_csrf()` before processing any request.

**Mechanism:**
1. On page load, the server generates a `secrets.token_hex(32)` token, stores it in the user's server-side session, and embeds it in the HTML as a `<meta name="csrf-token">` tag.
2. Every JavaScript `fetch()` call sends the token back in the `X-CSRF-Token` request header.
3. `_require_csrf()` compares the header value against `session["csrf_token"]`. If they do not match, the endpoint returns `403`.

```python
def _require_csrf():
    token = request.headers.get("X-CSRF-Token")
    if not token or token != session.get("csrf_token"):
        return jsonify({"error": "Invalid request"}), 403
    return None
```

---

### Braze Integration

The app integrates with Braze using two internal functions. Both always read `BRAZE_API_KEY`, `BRAZE_REST_ENDPOINT`, and `BRAZE_CAMPAIGN_ID` exclusively from environment variables. There is no mechanism for any user-supplied value to override the campaign ID.

#### `_braze_send(headline, subject, preheader, body, url, image_url=None)`

Triggers an **immediate** send via `POST /campaigns/trigger/send`. The caller now passes `subject` and `preheader` directly — the previous hard-coded `"Breaking news: <headline>"` prefix is gone. The Liquid template can choose to prefix or not.

The `url` field is passed through `_add_utm()` before being sent, which idempotently appends `utm_source=newsletter&utm_medium=email&utm_campaign=breaking-news` unless an `utm_source=` parameter is already present.

**Braze payload:**
```json
{
  "campaign_id": "<BRAZE_CAMPAIGN_ID>",
  "broadcast": true,
  "trigger_properties": {
    "headline": "<headline>",
    "subject": "<subject>",
    "preheader": "<preheader>",
    "body": "<body>",
    "url": "<url with utm params>",
    "image_url": "<image_url or empty string>"
  }
}
```

`broadcast: true` sends to all users subscribed to the campaign without requiring a list of recipient IDs.

#### `_braze_schedule(headline, subject, preheader, body, url, schedule_time, at_optimal_time=False, image_url=None)`

Schedules a send via `POST /campaigns/trigger/schedule/create`.

**Braze payload:**
```json
{
  "campaign_id": "<BRAZE_CAMPAIGN_ID>",
  "broadcast": true,
  "trigger_properties": { "...same as above..." },
  "schedule": {
    "time": "<ISO 8601 UTC datetime>"
  }
}
```

- `schedule.time` must be an ISO 8601 UTC datetime string that is **not in the past**.
- `at_optimal_time` is retained on the function signature for compatibility but is no longer used by any caller; intelligent-timing was removed in the iter-02 panel-review build (stakeholders said it wasn't needed).

Both functions raise an exception (which propagates as a 500 response) if the Braze API returns a non-2xx status.

---

### Article Fetching — `_MetaParser`

A lightweight HTML parser (subclass of `html.parser.HTMLParser`) that extracts Open Graph metadata from Guardian article pages.

**Extracts:**
- `og:title` → used as the headline (falls back to `<title>` tag)
- `og:description` → used as the body/preview text
- `og:image` → used as the image URL

After extraction, known Guardian title suffixes (` | The Guardian`, ` - The Guardian`) are stripped from the headline.

---

### Routes

#### `GET /`

Renders `index.html`. Generates a fresh CSRF token for the session on every page load. Reads `?role=sender|trainee|viewer` from the query string (defaults to `sender`; invalid values fall back to `sender`) and passes it to the template so the sidebar role chip can render and the JS can gate the send button.

```python
session["csrf_token"] = secrets.token_hex(32)
role = request.args.get("role", "sender")
return render_template("index.html", csrf_token=session["csrf_token"], role=role)
```

---

#### `GET /audit`

Renders `audit.html`, the activity page. Shows two tables:
1. **Pending scheduled sends** — every entry currently in `SCHEDULED_SENDS`, with a Cancel button per row.
2. **Recent activity** — the most recent 200 entries from `AUDIT_LOG`, with a client-side substring filter input above the table.

Both stores are module-level Python lists/dicts and reset on Flask restart (prototype only — no persistence).

---

#### `POST /api/send-test`

Mocks a test send. Same payload as `/api/send` plus a `test_recipient` string. In the current build, no real Braze test-call is made — the send is appended to `AUDIT_LOG` with `kind="test"` and `{"success": true}` is returned. Viewers are blocked (403). The compose page surfaces a clearly different (amber) success banner for test sends.

---

#### `POST /api/cancel-scheduled`

Body: `{ "id": "<scheduled-send-uuid>" }`. Removes the entry from `SCHEDULED_SENDS` and appends a `kind="cancel"` entry to `AUDIT_LOG` (referencing the cancelled id). Returns `{"success": true}` or 404 if id is unknown. No real Braze schedule-cancellation API call is made (prototype gap noted in the Deferred section).

---

#### `POST /api/check-duplicate`

Body: `{ "url": "https://..." }`. Looks through `AUDIT_LOG` for a `send` or `scheduled` entry with the same URL (ignoring `utm_*` params via `_strip_utm()`) within the last 6 hours. Returns `{ "duplicate": bool, "last_sent_at": iso_or_null }`. The compose page calls this after each successful article fetch and displays a non-blocking warning banner if a recent duplicate exists.

---

#### `POST /api/fetch-article`

Fetches a Guardian article URL and returns its headline, body, and image URL.

**Request body:**
```json
{ "url": "https://www.theguardian.com/..." }
```

**Validation:**
- CSRF token must be valid.
- URL scheme must be `https`.
- URL host must be exactly `www.theguardian.com`. No other domains are accepted.

**Process:**
1. Makes an HTTP GET to the article URL with a realistic browser User-Agent and `Accept-Language: en-GB`.
2. Feeds the HTML response through `_MetaParser`.
3. Strips Guardian suffixes from the headline.
4. Returns `{ "headline": "...", "body": "...", "image_url": "..." }`.

**Error response:** `{ "error": "<message>" }` with HTTP 400.

---

#### `POST /api/send`

Triggers a newsletter send via Braze.

**Request body:**
```json
{
  "headline": "Article headline (used inside the email body)",
  "subject": "Subject line shown in the recipient inbox",
  "preheader": "Preview text shown alongside the subject in the inbox",
  "body": "Body / summary text",
  "url": "https://www.theguardian.com/...",
  "image_url": "https://...",
  "timing": "immediate" | "scheduled",
  "sched_at": "2026-05-15T13:30:00",  // required only when timing=scheduled
  "role": "sender" | "trainee" | "viewer"
}
```

**Timing mode behaviour:**

| Mode | Backend action |
|---|---|
| `immediate` | Calls `_braze_send()` — sends right now |
| `scheduled` | Calls `_braze_schedule()` with `sched_at` as the time. Returns 400 if `sched_at` is missing. `sched_at` is a bare UTC ISO-8601 string (`YYYY-MM-DDTHH:MM:SS`) converted from the user's local date/time by the browser. Also adds an entry to `SCHEDULED_SENDS` so it can be cancelled from `/audit`. |

Intelligent timing mode has been removed (stakeholders said it wasn't needed).

**Role behaviour:**

| Role | Backend action |
|---|---|
| `sender` | Full send — calls Braze if `BRAZE_API_KEY` set; writes `kind="send"` (or `"scheduled"`) audit entry. |
| `trainee` | Dry-run — Braze never called regardless of API key; writes `kind="trainee_practice"` audit entry; does not register a pending scheduled send. The compose page shows an amber "Practice send recorded (Braze not called)" banner. |
| `viewer` | Endpoint returns 403. Compose page disables the send + send-test buttons. |

**Dev mode bypass:** If `BRAZE_API_KEY` is not set, the endpoint still writes an audit entry but skips the Braze call. This allows local development without credentials.

**Success response:** `{ "success": true }`
**Error response:** `{ "success": false, "error": "<message>" }` with HTTP 400 or 500.

---

## Frontend (`templates/index.html`)

### Layout

The UI is a fixed-height single-page app with three structural zones:

```
┌──────────┬────────────────────────────┬──────────────┐
│  Sidebar │  Form Panel (scrollable)   │ Preview Panel│
│  (60px)  │                            │  (300px)     │
└──────────┴────────────────────────────┴──────────────┘
```

On viewports narrower than 900px the layout stacks: the preview panel (and its Send button) renders full-width below the form panel and the page becomes scrollable.

---

### Design System (`static/guardian.css`)

A CSS custom property stylesheet providing Guardian-branded design tokens:

- **Colours:** `--guardian-blue` (`#052962`), `--guardian-blue-bright` (`#1556b0`), `--guardian-news-red` (`#c70000`), ink scale (`--ink-900` through `--ink-50`).
- **Typography:** `--font-sans` (Guardian Sans fallback chain), `--font-serif` (Guardian Egyptian / Source Serif 4 fallback chain). Source Serif 4 is loaded from Google Fonts.
- **Spacing/radius/shadow tokens** for consistent component styling.

---

### Form Sections

#### Content Card

Fields appear in this order to match the recipient mental model (inbox → opened email):

- **Guardian article URL field** — freetext input. Triggers `onUrlInput()` on each keystroke; on success populates the next fields and runs a duplicate check.
- **Subject line** — text input, max 200 characters (was 100). Character counter warns at 180. Default value `"Breaking news: "` is pre-filled but fully editable, including removing the prefix. A field-hint reads "Shown in the recipient's inbox subject line."
- **Preheader** — text input, max 100 characters. Field-hint: "Inbox preview text shown next to the subject."
- **Article headline** — text input. Field-hint: "Displayed inside the email body as the main heading." Fed from `og:title` after fetch.
- **Body / preview text** — textarea, max 280 characters.
- **Image URL** — text input pre-filled from `og:image`. Adjacent "Use article image" ghost button restores the original fetched image if the user edits it and wants to revert.
- **Duplicate-warning banner** — hidden by default; shown above the card when `/api/check-duplicate` reports a recent same-URL send. Copy uses "earlier today at HH:MM" or "yesterday at HH:MM".

#### Channel Card

Displays a fixed informational panel showing the delivery channel: "Newsletter — Email via Braze". No user interaction; the channel is not configurable.

#### Audience Segments Card

Displays five segment toggle buttons: United Kingdom, United States, Australia, Europe, Global (ALL).

> **Important:** Segment selection is UI-only and not wired to the backend. The warning card in the UI makes this explicit. All sends go to the same Braze campaign regardless of which segments are selected. Segment targeting is marked as "Not in production".

The segment state is tracked in `state.segments` (a plain object keyed by segment ID). `updateSendButton()` requires at least one selected segment before the send button enables. Selected segment labels are included in the send payload and recorded in the audit log (still not used for Braze targeting).

#### Delivery & Timing Card

Two mutually exclusive timing mode buttons (intelligent timing has been removed):
1. Immediate
2. Scheduled

Selecting a mode updates visual state, shows/hides the date/time picker, updates routing detail text, and re-evaluates the send button.

**Scheduled sub-panel:** Shows a date input and a time input (both in the user's local time). On send, these are combined and converted to UTC ISO-8601 via `new Date(...).toISOString().slice(0, 19)`.

#### Test-send mini-card

Sits below the Delivery & Timing card, inside the form panel (deliberately not in the right rail where the primary Send button lives — this is to prevent accidental clicks under pressure). Dashed border, amber accent, "🧪" prefix on the button. Contains:
- **Test recipient** input — pre-filled with `test@theguardian.com`, editable.
- **🧪 Send test email** button — posts to `/api/send-test`. Success banner is amber to differentiate from the green real-send banner.

---

### JavaScript State

```javascript
const state = {
  segments: {},        // { uk: true, us: false, ... }
  timing: 'immediate' | 'scheduled',
  role: 'sender' | 'trainee' | 'viewer',
  sendingTest: false,
  articleImageUrl: ''  // cached og:image, used by "Use article image" restore button
};
```

---

### Key JavaScript Functions

| Function | Purpose |
|---|---|
| `init()` | Builds segment buttons dynamically from the `SEGMENTS` array and calls `updateSendButton()`. |
| `onUrlInput()` | Debounces URL input by 500ms then calls `fetchArticle()`. |
| `fetchArticle(url)` | POSTs to `/api/fetch-article`, populates headline and body fields on success, shows status message. |
| `toggleSegment(id)` | Toggles a segment in `state.segments`, updates button appearance, hint text, preview pills, and send button. |
| `selectTiming(t)` | Sets `state.timing`, updates timing button classes, shows/hides sub-panels, updates routing detail. |
| `updatePreview()` | Syncs the inbox-preview stripe (subject + preheader) and opened-email mock (headline, image with error fallback, body) with current field values. |
| `updateCharCount(inputId, countId, max)` | Updates character count display and applies warning/over CSS classes. |
| `updateSendButton()` | Enables/disables send button based on: subject non-empty, at least one segment, and (if scheduled) a date+time in the future. Warns when the article URL is empty. Disarms a pending confirm on any form change. |
| `sendAlert()` | Two-step: first call arms the button ("Confirm: send to N segments", auto-disarms after 8s/Esc/cancel link); second call locks the button ("Sending…") and POSTs to `/api/send`. Shows success banner on success, red error banner on failure. Resets button 3 seconds after success. |
| `saveDraft()` / `restoreDraft()` | Snapshot all form fields, segments and timing into `sessionStorage` before a role-change reload; restore (one-shot) on init, re-running the duplicate check if a URL is present. |
| `showBanner(kind, title, sub)` | Renders the shared banner in success / test / practice / error variants. |
| `dismissSuccess()` | Hides the banner. |

---

### CSRF on the Frontend

The CSRF token is read from the `<meta name="csrf-token">` tag on page load:

```javascript
const CSRF = document.querySelector('meta[name="csrf-token"]').content;
```

Every `fetch()` call includes it as a header:

```javascript
headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': CSRF }
```

---

### Email Preview Panel

The right-hand panel renders a live miniature email mockup:
- Header bar: navy background, "D" logo, "The Guardian" brand name.
- Headline: updates in real time as the user types, prefixed with "Breaking news: ".
- Body: updates in real time.
- CTA button: static "Read more →" link (not functional in preview).

Below the email mockup, the panel shows:
- **Routing:** channel name and timing detail (updates when timing mode changes).
- **Sending to:** pills for each selected segment.
- **Send button:** state-aware (disabled/ready/armed/sending/sent), label changes per timing mode and role; arming requires a second click to confirm before anything is dispatched.

---

### Success Banner

A green banner shown after a successful send. Content varies by timing mode:

| Mode | Banner title |
|---|---|
| immediate | "Breaking news email sent" |
| scheduled | "Breaking news email scheduled for `<date> <time>` (local)" |
| intelligent | "Breaking news email queued for intelligent delivery" |

Dismissed by clicking the × button.

---

## Braze Campaign Requirements

The Braze campaign referenced by `BRAZE_CAMPAIGN_ID` must be configured as follows:

- **Delivery type:** API-Triggered Delivery (not scheduled, not action-based).
- **Audience:** set to broadcast or the intended subscriber list.
- **Trigger properties:** the campaign template must reference the following Liquid variables passed via `trigger_properties`:
  - `{{trigger_properties.headline}}`
  - `{{trigger_properties.subject}}`
  - `{{trigger_properties.body}}`
  - `{{trigger_properties.url}}`
  - `{{trigger_properties.image_url}}`

The Braze API key must have the following endpoint permissions enabled:
- `campaigns.trigger.send`
- `campaigns.trigger.schedule.create`

---

## Deployment (Render)

Defined in `render.yaml`:

```yaml
services:
  - type: web
    name: dispatch
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

Environment variables (`BRAZE_API_KEY`, `BRAZE_CAMPAIGN_ID`, `BRAZE_REST_ENDPOINT`, `SECRET_KEY`) must be set in the Render dashboard under the service's environment settings. They are not committed to the repository.

---

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with required variables (see Environment Variables section)

# Start development server (defaults to port 5050)
python app.py
```

If `BRAZE_API_KEY` is absent from `.env`, sends will return success without hitting Braze, allowing safe UI development.

---

## Security Notes

- **CSRF protection** is applied to all state-changing endpoints.
- **URL allowlist:** article fetching is restricted to `https://www.theguardian.com` only. No other domains can be fetched.
- **Campaign ID is not user-controllable.** It is read exclusively from the environment. There is no API parameter that can redirect sends to a different campaign.
- **Secrets** are never embedded in the frontend or committed to source control.

---

## MVP scope vs. stakeholder requirements

This build addresses the top-voted stakeholder requirements (see `Breaking news tool newsletters requriement.md`). The panel-review loop in `panel-review-v1/` records the iter-01 → iter-02 review by Priya (UX) and Tom (editorial user); iter-02 was accepted.

**Included in MVP (most popular themes):**

| Theme | Votes |
|---|---|
| Preview & testing (preheader render, image swap, send-test) | 7 |
| Access control (mock Sender/Trainee/Viewer role chip) | 4 |
| Tracking & monitoring (audit log + UTM tracking) | 4 |
| Subject-line customisation (200-char cap, editable prefix, preheader) | 3 |
| Schedule handling (intelligent removed, cancel scheduled from /audit) | 3 |
| Duplicate detection (6h window, non-blocking banner) | 2 |
| Simpler interface (single page, mental-model field order) | 2 |

**Deferred (noted, not built):**

- Performance benchmarks & best-practice timings.
- Dependency / vulnerability review.
- 24/7 support coverage and ownership policy.
- Mandatory training process gate (only the role picker is mocked).
- Backup/fallback plan if Braze is unavailable.
- Legal/Braze T&Cs review.
- Braze session management.
- Composer integration.
- Opt-out category UI (newsletter opt-out remains managed inside Braze).
- Live-blog specific block selector.
- Send-corrections dedicated flow.
- Real Braze API test-send (currently mocked — `/api/send-test` only writes to the audit log).
- Real Braze schedule cancellation (currently drops from in-memory store and audit-logs the action).
- Persistence across server restarts (`AUDIT_LOG` and `SCHEDULED_SENDS` are module-level, reset on restart).
