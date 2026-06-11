from flask import Flask, render_template, jsonify, request, session
from html.parser import HTMLParser
from html import unescape
from urllib.parse import urlparse, urlencode, parse_qsl, urlunparse
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import requests as http
import secrets
import uuid
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

_GUARDIAN_HOST = "www.theguardian.com"
_VALID_ROLES = ("sender", "trainee", "viewer")

# ── In-memory stores (dev / prototype only) ──────────────
AUDIT_LOG = []          # list of dicts, newest first
SCHEDULED_SENDS = {}    # id -> entry dict


def _require_csrf():
    token = request.headers.get("X-CSRF-Token")
    if not token or token != session.get("csrf_token"):
        return jsonify({"error": "Invalid request"}), 403
    return None


def _add_utm(url):
    """Idempotently append Dispatch UTM params to a URL. No-op if utm_source= present."""
    if not url:
        return url
    parsed = urlparse(url)
    query = parsed.query or ""
    if "utm_source=" in query:
        return url
    extra = "utm_source=newsletter&utm_medium=email&utm_campaign=breaking-news"
    new_query = (query + "&" + extra) if query else extra
    return urlunparse(parsed._replace(query=new_query))


def _strip_utm(url):
    """Return url with any utm_* params removed — used for duplicate comparison."""
    if not url:
        return url
    parsed = urlparse(url)
    pairs = [(k, v) for (k, v) in parse_qsl(parsed.query, keep_blank_values=True) if not k.startswith("utm_")]
    new_query = urlencode(pairs)
    return urlunparse(parsed._replace(query=new_query))


def _braze_send(headline, subject, preheader, body, url, image_url=None):
    api_key = os.environ.get("BRAZE_API_KEY", "")
    endpoint = os.environ.get("BRAZE_REST_ENDPOINT", "https://rest.fra-01.braze.eu")
    campaign_id = os.environ.get("BRAZE_CAMPAIGN_ID", "")

    if not api_key:
        raise ValueError("BRAZE_API_KEY not set")
    if not campaign_id:
        raise ValueError("BRAZE_CAMPAIGN_ID not set")

    tracked_url = _add_utm(url)

    payload = {
        "campaign_id": campaign_id,
        "broadcast": True,
        "trigger_properties": {
            "headline": headline,
            "subject": subject,
            "preheader": preheader,
            "body": body,
            "url": tracked_url,
            "image_url": image_url or "",
        },
    }

    resp = http.post(
        f"{endpoint}/campaigns/trigger/send",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=15,
    )
    if not resp.ok:
        print("Braze error:", resp.status_code, resp.text)
    resp.raise_for_status()
    return resp.json()


def _braze_schedule(headline, subject, preheader, body, url, schedule_time, at_optimal_time=False, image_url=None):
    api_key = os.environ.get("BRAZE_API_KEY", "")
    endpoint = os.environ.get("BRAZE_REST_ENDPOINT", "https://rest.fra-01.braze.eu")
    campaign_id = os.environ.get("BRAZE_CAMPAIGN_ID", "")

    if not api_key:
        raise ValueError("BRAZE_API_KEY not set")
    if not campaign_id:
        raise ValueError("BRAZE_CAMPAIGN_ID not set")

    schedule = {"time": schedule_time}
    if at_optimal_time:
        schedule["at_optimal_time"] = True

    tracked_url = _add_utm(url)

    payload = {
        "campaign_id": campaign_id,
        "broadcast": True,
        "trigger_properties": {
            "headline": headline,
            "subject": subject,
            "preheader": preheader,
            "body": body,
            "url": tracked_url,
            "image_url": image_url or "",
        },
        "schedule": schedule,
    }

    resp = http.post(
        f"{endpoint}/campaigns/trigger/schedule/create",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=15,
    )
    if not resp.ok:
        print("Braze error:", resp.status_code, resp.text)
    resp.raise_for_status()
    return resp.json()


class _MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.og_title = None
        self.og_description = None
        self.og_image = None
        self._title_buf = []
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta":
            prop = attrs.get("property") or attrs.get("name") or ""
            content = attrs.get("content", "")
            if prop == "og:title" and not self.og_title:
                self.og_title = content
            elif prop == "og:description" and not self.og_description:
                self.og_description = content
            elif prop == "og:image" and not self.og_image:
                self.og_image = content
        elif tag == "title":
            self._in_title = True

    def handle_data(self, data):
        if self._in_title:
            self._title_buf.append(data)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    @property
    def title(self):
        return "".join(self._title_buf).strip()


@app.route("/api/fetch-article", methods=["POST"])
def fetch_article():
    err = _require_csrf()
    if err:
        return err

    url = (request.json or {}).get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != _GUARDIAN_HOST:
        return jsonify({"error": "Only Guardian article URLs are supported"}), 400

    try:
        resp = http.get(url, timeout=8, headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-GB,en;q=0.9",
        })
        resp.raise_for_status()
        parser = _MetaParser()
        parser.feed(resp.text)
        headline = unescape(parser.og_title or parser.title or "")
        for suffix in (" | The Guardian", " - The Guardian"):
            if suffix in headline:
                headline = headline.split(suffix)[0].strip()
                break
        body = unescape(parser.og_description or "")
        image_url = parser.og_image or ""
        return jsonify({"headline": headline, "body": body, "image_url": image_url})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/")
def index():
    session["csrf_token"] = secrets.token_hex(32)
    role = request.args.get("role", "sender")
    if role not in _VALID_ROLES:
        role = "sender"
    return render_template("index.html", csrf_token=session["csrf_token"], role=role)


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _append_audit(entry):
    AUDIT_LOG.insert(0, entry)


@app.route("/api/send", methods=["POST"])
def send_alert():
    err = _require_csrf()
    if err:
        return err

    data = request.json or {}
    headline = data.get("headline", "")
    subject = data.get("subject", "") or headline
    preheader = data.get("preheader", "")
    body = data.get("body", "")
    url = data.get("url", "")
    image_url = data.get("image_url", "")
    timing = data.get("timing", "immediate")
    sched_at = data.get("sched_at")  # bare UTC ISO-8601, e.g. "2026-05-15T13:30:00"
    segments = [s for s in (data.get("segments") or []) if isinstance(s, str)][:10]
    role = data.get("role", "sender")
    if role not in _VALID_ROLES:
        role = "sender"

    if role == "viewer":
        return jsonify({"success": False, "error": "Read-only role cannot dispatch newsletters"}), 403

    # Trainee role: dry-run — audit entry kind="trainee_practice", Braze never called.
    is_trainee = (role == "trainee")
    has_braze = bool(os.environ.get("BRAZE_API_KEY")) and not is_trainee

    try:
        if timing == "immediate":
            if has_braze:
                _braze_send(headline, subject, preheader, body, url, image_url)
            entry = {
                "id": str(uuid.uuid4()),
                "ts": _now_iso(),
                "role": role,
                "kind": "trainee_practice" if is_trainee else "send",
                "timing": "immediate",
                "headline": headline,
                "subject": subject,
                "preheader": preheader,
                "url": url,
                "segments": segments,
                "status": "ok",
            }
            _append_audit(entry)
        elif timing == "scheduled":
            if not sched_at:
                return jsonify({"success": False, "error": "Schedule time is required"}), 400
            try:
                sched_dt = datetime.strptime(sched_at, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                return jsonify({"success": False, "error": "Invalid schedule time format"}), 400
            if sched_dt < datetime.now(timezone.utc) - timedelta(minutes=1):
                return jsonify({"success": False, "error": "Scheduled time is in the past — pick a future time"}), 400
            if has_braze:
                _braze_schedule(headline, subject, preheader, body, url, sched_at, image_url=image_url)
            sid = str(uuid.uuid4())
            entry = {
                "id": sid,
                "ts": _now_iso(),
                "role": role,
                "kind": "trainee_practice" if is_trainee else "scheduled",
                "timing": "scheduled",
                "sched_at": sched_at,
                "headline": headline,
                "subject": subject,
                "preheader": preheader,
                "url": url,
                "segments": segments,
                "status": "ok",
            }
            # Trainee practice: do not register a real pending scheduled send.
            if not is_trainee:
                SCHEDULED_SENDS[sid] = entry
            _append_audit(dict(entry))
        else:
            return jsonify({"success": False, "error": "Unknown timing mode"}), 400
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

    return jsonify({"success": True, "trainee_practice": is_trainee})


@app.route("/api/send-test", methods=["POST"])
def send_test():
    err = _require_csrf()
    if err:
        return err

    data = request.json or {}
    headline = data.get("headline", "")
    subject = data.get("subject", "") or headline
    preheader = data.get("preheader", "")
    url = data.get("url", "")
    test_recipient = (data.get("test_recipient") or "").strip()
    role = data.get("role", "sender")
    if role not in _VALID_ROLES:
        role = "sender"

    if role == "viewer":
        return jsonify({"success": False, "error": "Read-only role cannot send test emails"}), 403

    if not test_recipient:
        return jsonify({"success": False, "error": "Test recipient is required"}), 400

    # Dev-mode: mock Braze test send. Real Braze test sending TBD.
    entry = {
        "id": str(uuid.uuid4()),
        "ts": _now_iso(),
        "role": role,
        "kind": "test",
        "timing": "immediate",
        "headline": headline,
        "subject": subject,
        "preheader": preheader,
        "url": url,
        "test_recipient": test_recipient,
        "segments": [s for s in (data.get("segments") or []) if isinstance(s, str)][:10],
        "status": "ok",
    }
    _append_audit(entry)
    return jsonify({"success": True})


@app.route("/audit")
def audit():
    session["csrf_token"] = session.get("csrf_token") or secrets.token_hex(32)
    role = request.args.get("role", "sender")
    if role not in _VALID_ROLES:
        role = "sender"
    return render_template(
        "audit.html",
        csrf_token=session["csrf_token"],
        audit_log=AUDIT_LOG[:200],
        scheduled=list(SCHEDULED_SENDS.values()),
        role=role,
    )


@app.route("/api/cancel-scheduled", methods=["POST"])
def cancel_scheduled():
    err = _require_csrf()
    if err:
        return err

    data = request.json or {}
    sid = data.get("id")
    if not sid or sid not in SCHEDULED_SENDS:
        return jsonify({"success": False, "error": "Not found"}), 404

    removed = SCHEDULED_SENDS.pop(sid)
    _append_audit({
        "id": str(uuid.uuid4()),
        "ts": _now_iso(),
        "role": data.get("role", "sender"),
        "kind": "cancel",
        "timing": "n/a",
        "headline": removed.get("headline", ""),
        "subject": removed.get("subject", ""),
        "preheader": removed.get("preheader", ""),
        "url": removed.get("url", ""),
        "cancelled_id": sid,
        "status": "ok",
    })
    return jsonify({"success": True})


@app.route("/api/check-duplicate", methods=["POST"])
def check_duplicate():
    err = _require_csrf()
    if err:
        return err

    data = request.json or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"duplicate": False, "last_sent_at": None})

    target = _strip_utm(url)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=6)

    last_ts_iso = None
    for entry in AUDIT_LOG:
        if entry.get("kind") not in ("send", "scheduled"):
            continue
        if _strip_utm(entry.get("url", "")) != target:
            continue
        try:
            ts = datetime.strptime(entry["ts"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except Exception:
            continue
        if ts >= cutoff:
            last_ts_iso = entry["ts"]
            break

    return jsonify({"duplicate": last_ts_iso is not None, "last_sent_at": last_ts_iso})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port)
