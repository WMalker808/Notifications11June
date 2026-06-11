# Iter-01 feedback

## Verdict: REJECT

Two real blockers (field order, send/test confusability) plus several worth-fixing items. Both panellists answered NO to at least one acceptance question.

---

## Priya (UX designer)

**Verdict:** REJECT
**Q1 (confident <60s send):** YES — the form is short, the preview is live, the buttons are clear once you find them.
**Q2 (features present/usable):** NO — preheader, send-test, audit log, role gating and dup-detection are all wired up, but the field order breaks the mental model the brief itself specified, and "Image URL" is not really "image replacement ease".

### Blocking issues
- **Field order is wrong vs. the brief.** The changelog says the intended order is `URL → subject → preheader → headline → body → image → segments → timing → send`, but the rendered form is `URL → subject → preheader → image-url → headline → body → segments → timing`. Image is *above* the headline, which is confusing — image is a decoration of the article, the headline is the article. More importantly, "Subject line" sits directly under "Guardian article URL" with no visual cue that the subject was auto-derived from the headline lower down. A user who customises the subject before scrolling down can't see what the underlying headline says.
- **"Subject line" vs "Article headline" is genuinely ambiguous.** The labels are clear in isolation, but in the rendered page they look like two near-identical text inputs. Both default to populated values after a URL fetch, both feed the preview, both have character counters. A first-time user will not know which one ends up in the recipient's inbox without reading the helper text — and there is no helper text. Subject needs a one-liner under the label: "Shown in inbox subject line. Headline below is used inside the email body."

### Nits (non-blocking)
- The role picker is a tiny native `<select>` jammed at the bottom of a 60px-wide navy sidebar. It works, but it doesn't *look* like "this is who I am" — more like an afterthought. A labelled chip ("Role: Sender") would be more legible.
- Audit page has no sidebar. It uses the same fonts and card style, but the missing navy sidebar makes it feel like a different tool. The "← Back to Dispatch" link is fine, but the visual continuity is broken.
- "Image URL" is a plain text input. The requirement explicitly says "Image replacement ease". Pasting a URL is not easy replacement — there's no upload, no thumbnail preview next to the field (the only preview is in the right-hand mock email), no "use article default" button to restore the `og:image`.
- Preview shows the subject in serif headline style at 17px. That's not what the recipient sees in their inbox — the subject is rendered by their mail client, not by Guardian typography. The preview is currently mocking the *opened* email; the subject + preheader pair is what matters in the inbox list, and that's not being mocked.
- Empty state before URL paste: subject defaults to `"Breaking news: "` (with trailing space) and the preview shows `"Breaking news: Your subject line"`. Fine, but the preheader placeholder reads `"Shown in inbox preview"` in the preview too — looks like real content for a second.
- Duplicate warning copy: "This URL was already sent at HH:MM today" — the JS uses `toLocaleTimeString` on a UTC ISO timestamp. That converts correctly, but the word "today" is hard-coded — if a dup was sent yesterday within 6 hours, it still says "today".

---

## Tom (editorial user)

**Verdict:** REJECT
**Q1 (confident <60s send):** NO — I can get there in 60s on a calm day, but two things would catch me at 3am: I cannot tell at a glance which button is Send and which is Test, and the Trainee role doesn't actually do what training implies.
**Q2 (features present/usable):** YES — preheader is there, dup-warn fires, audit log is real, role gating returns a 403, test-send writes to the log. They're present.

### Blocking issues
- **Send vs Send-test are too similar and stacked vertically.** Send Newsletter (navy, filled) sits directly above Send test email (white, navy outline). Under pressure I scan for "the big button" — I will hit the top one. If I'm sending a test I might overshoot and hit the real Send. Worse, the test button has no confirmation and no "TEST" badge, and the success banner for both uses the same green tick — the only difference is the title text. The test button should either (a) live in a clearly different region (e.g. inside the form panel near content, not stacked under the live Send button), or (b) get a very different visual treatment (smaller, dashed border, "🧪 TEST" badge).
- **Trainee role is a lie.** The picker offers Sender / Trainee / Viewer, but Trainee behaves identically to Viewer — server returns 403, button is disabled, hint says "Read-only role — switch to Sender to send." The requirement explicitly calls out "Training required before access". A Trainee should be able to *practice* the full flow (compose, dup-check, test-send) with the real Send gated. Right now there's no point being Trainee instead of Viewer.

### Nits (non-blocking)
- "Braze" appears four times on the compose page: channel card ("Email via Braze"), channel badge ("Braze"), routing detail ("Immediate send via Braze"), and routing badge ("Braze"). The brief asked for plain English with no Braze leakage. The backend can be Braze; the user-facing copy should say "Email" or "Newsletter system". Minor, but it's a tell that this is a dev prototype.
- Audit log is scannable but not searchable. No filter by role, kind, or URL substring. For "did Sarah send the same link 10 minutes ago" I'd have to eyeball a table that could grow to 200 rows. Even a single text filter input would help. (Acknowledged — dup-warn on the compose page handles the most urgent version of this question.)
- Cancelling a scheduled send uses a `window.confirm()` browser dialog — fine functionally, fast (one click + OK), but a tired editor could OK-by-reflex. The confirm message just says "Cancel this scheduled send?" — no headline or scheduled time in the prompt. Worth showing *what* is being cancelled.
- Test recipient field is pre-filled with `test@theguardian.com`. Good (one less step). But the field is small (12px font, jammed next to the label) — easy to miss that it's editable. If I want to send a test to my own address I might not notice I can change it.
- Role-change reload is a full page navigation. Loses any in-progress draft. Under pressure, if I switch role to check what Trainee sees, my URL/subject/body all evaporate. Builder flagged this as known.
- No "delivery confirmation" anywhere in the UI for an immediate send. The success banner says "Breaking news email sent" — but did Braze accept it? Was it 200 OK? The audit log will show `status: ok` but I don't see that on the compose page. The current behaviour silently swallows whether Braze actually accepted (only an exception surfaces).
- No segments are selected by default and the send button stays disabled until at least one is — but `updateSendButton()` has `const hasSegment = true;` hard-coded. Selecting no segments still produces a "ready" button as long as subject is non-empty. The hint "Select at least one segment" never fires from the actual state. This is a real bug, not a nit — but I'm putting it here because Tom would only notice it when sending with zero segments and the system happily lets him through.

---

## Summary for next Builder

Top fixes for iter-02 (in priority order):

1. **Reorder fields** to match the brief: URL → subject → preheader → headline → body → image → channel → segments → timing. Add a one-line helper under "Subject line" clarifying it is the inbox subject and "Article headline" is used inside the body.
2. **Differentiate Send vs Send-test.** Move test-send out of the right-rail Send region, or give it a visually distinct treatment (smaller, dashed, "TEST" badge) and a different success banner colour. Stacking two big buttons together is the 3am-mistake setup.
3. **Make Trainee actually do something.** At minimum, dry-run mode: full flow works, writes a `kind=trainee_practice` audit entry, no Braze call. Otherwise drop the Trainee option from the picker.
4. **Fix the segment-required check.** `updateSendButton()` has `const hasSegment = true;` hard-coded — should be `Object.values(state.segments).some(Boolean)`. Currently the brief's "select at least one segment" rule is not enforced.
5. **Tone down "Braze" in user-facing copy.** Replace channel/routing labels with "Email" or "Newsletter system". Backend identity is fine in code; not in UI text.

Nice-to-haves if time: audit-page text filter, scheduled-cancel confirmation that names what is being cancelled, an "Image: use article default" button, dup-warn copy that doesn't hard-code "today".
