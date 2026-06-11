# Panel review v2 — iter-02 feedback

**Build under review:** iter-02 changes, running locally; both panellists re-walked the 3am scenario, the trainee→sender promotion flow, and the audit/cancel flow.

## Verdict: REJECT (narrowly) — blockers all fixed, but two of the fixes have gaps the panel won't wave through on a send-to-everyone tool.

---

## Asha (UX usability expert)

**Q1 (confident <60s send, nothing by accident): YES.** The arm-then-confirm button is the right pattern — it adds one click, not a modal, and the red arm state + named segments make the final gesture deliberate. Preview now changes when I type a headline; the inbox stripe finally explains why subject and preheader are separate fields.

**Q2 (UI state tells the truth): ALMOST.**

### Remaining issues

**A10 (must-fix). The restored draft skips the duplicate check.**
This is the gap in the A5 fix, and it matters precisely in the intended workflow: a trainee drafts a practice send for a URL that was already sent an hour ago — dup banner shows. They switch to Sender to send it for real. After the reload the draft is faithfully restored but `checkDuplicate()` never re-runs, so the duplicate warning — a safety feature — silently vanishes at the exact moment the send becomes real. Re-run the dup check (and ideally re-show the fetch status) when a draft with a URL is restored.

**A11 (should-fix). The confirm prompt is invisible to screen-reader users.**
The armed state communicates entirely through `#send-btn` text and `#send-hint` repaints. Neither region is `aria-live`, so a screen-reader user hears nothing when the button arms — they click "Send", nothing announces "Confirm: send to 2 segments", they click again… which is exactly the double-press we're guarding against, except now it completes the send. `aria-live="polite"` on the hint (and the banner) is a one-attribute fix.

### Nits (non-blocking)
- The kind-pill row renders on an empty audit log, filtering nothing. Hide it when there's no table.
- Restored drafts lose the "✓ Article metadata loaded" status line — cosmetic, the fields themselves are intact.

---

## Jonah (editorial tools designer)

**Q1: YES.** Double-click is dead: I hammered the button — one request. Past-schedule is rejected client-side with a reason and server-side with a 400. Audit log now answers "who got this?" via the Segments column, and the pills give me "only real sends" in one click.

**Q2: ALMOST.**

### Remaining issues

**J10 (must-fix). The armed hint eats the no-URL warning.**
Iter-01 J4 asked for the missing-URL warning to be restated at the confirm step. In this build the ready-state hint warns correctly, but the moment you click Send, `_armSend()` overwrites the hint with "Sends now to United Kingdom. Click again to confirm." — the warning disappears at the exact moment the user is deciding whether to commit. The armed hint must carry the warning through: "Sends now to United Kingdom — ⚠ no article URL. Click again to confirm."

### Nits (non-blocking)
- Cancel flow on the audit page still uses native `confirm()` — fine for now, it's at least localised and names the send.
- `state.sendingTest` and the new `state.sending` are separate locks; a test send and a real send can be in flight simultaneously. Harmless (different endpoints, different buttons) but worth a comment if it ever bites.
- Segments column shows the *labels* sent by the client, not validated server-side against a known list. Prototype-acceptable; flag for the real build.

---

## Required for ACCEPT
A10 (dup check on draft restore), J10 (no-URL warning survives arming), A11 (aria-live on hint + banner). The two nits about empty-log pills and restored status line are at builder's discretion.
