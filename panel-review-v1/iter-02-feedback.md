# Iter-02 feedback

## Verdict: ACCEPT

Both iter-01 blockers (field order + subject/headline ambiguity for Priya; send-vs-test confusion + dead Trainee role for Tom) are fixed. The segment-required bug is fixed. Braze leakage in user-facing copy is gone. Audit page now has the sidebar and a text filter. Cancel-confirm names what's being cancelled. Dup-warn no longer hard-codes "today". Both panellists answer YES to both acceptance questions, with the nits below as polish for a later pass — none are 3am-blockers.

---

## Priya (UX designer)

**Verdict:** ACCEPT
**Q1 (confident <60s send):** YES — clearer than iter-01. URL → subject (with helper) → preheader (with helper) → headline (with helper) → body → image-with-restore. The eye now flows from "what the recipient sees in their inbox" down to "what they see when they open it", which mirrors the mental model.
**Q2 (features present/usable):** YES — preheader, send-test, audit log, role gating, dup-detection, trainee-mode, segment-gate, and reduced-Braze copy are all present and behave the way the brief implies. The "Use article image" ghost button is a real improvement on plain-URL paste.

### Nits (non-blocking)
- The role-chip in the sidebar is much better than the bare `<select>`. One small thing: the chip text is centred but the chevron from the native select is invisible (opacity:0 overlay). Hover doesn't visibly hint that the chip is clickable. A tiny ▾ glyph next to the role label would make the affordance obvious. Not blocking — the cursor change on hover gets you there.
- The test-send mini-card row crams "To" label + email input + "🧪 Send test email" button on one line. At narrow widths it'll wrap awkwardly. On a 1280px screen at the prototype's current 300px right rail it's fine; if the form panel ever narrows it'll get tight. Worth keeping in mind, not worth fixing now.
- The email preview still renders the *opened* email (headline at 17px serif, body, CTA) but does not mock the *inbox preview* (subject + preheader pair as Gmail/Outlook would show them). The preheader is now in the preview, which is progress, but a small "Inbox preview" stripe above the opened-mail mock would close the loop on why these two fields matter. Future polish.
- "Image URL" is still a paste-a-URL field with no thumbnail next to the input. The right-rail preview shows the image, so the user does get a visual check — just not adjacent to the field. Acceptable; the "Use article image" restore button addresses the bigger half of "image replacement ease".
- `.route-braze` is still the CSS class name on the routing badge (the visible text is now "Email"). Purely internal — no user-facing leakage.

---

## Tom (editorial user)

**Verdict:** ACCEPT
**Q1 (confident <60s send):** YES — at 3am the test button is now mid-form in a dashed amber-bordered card with "🧪", while Send Newsletter is alone in the right rail in solid navy. They no longer look like "stacked siblings". Practice/test success banners go amber, real-send banner stays green — different colour means I know what just happened without reading.
**Q2 (features present/usable):** YES — preheader works, dup-warn fires with "earlier today" / "yesterday" wording, audit log has a substring filter, role gating returns 403 for viewer, trainee can do a full dry-run flow that writes `trainee_practice` to the log and never calls Braze, segment-required check actually fires now.

### Nits (non-blocking)
- A scheduled trainee practice doesn't show up in the Pending scheduled sends table — by design (it's a dry run, no real schedule). That's the right call, but a trainee finishing a "practice schedule" might wonder where it went. The success banner saying "nothing was delivered to subscribers" half-answers this; "nothing was scheduled either" would be more precise. One-line copy tweak.
- Role-change is still a full page reload that loses the draft. Builder flagged it iter-01 as known. Live with it for the workshop; revisit before any real rollout.
- No delivery confirmation banner on the compose page beyond "Breaking news email sent". The audit log shows `status: ok` immediately, so a power user can verify. Fine for prototype.
- Cancel confirm now reads `Cancel the scheduled send "<headline>"?\n\nScheduled for <ts>.` — the timestamp is the raw UTC ISO string (`2026-06-08T18:30:00`). Readable but ugly. A local-formatted time would be friendlier. Not blocking.
- Audit-log filter is substring across the row's textContent. Works for "did Sarah send this URL". Doesn't help if a user wants "show me only test-sends" without typing "test" (which also matches `test@theguardian.com` in role/recipient columns if those ever surface). A kind-pill toggle row above the table would be cleaner. Future.

---

No blockers from either panellist. Ship iter-02.
