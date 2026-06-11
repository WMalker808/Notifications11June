# Panel review v2 — iter-03 feedback

**Build under review:** iter-03 changes, running locally.

## Verdict: ACCEPT

Both panellists answer YES to both acceptance questions. All iter-02 must-fixes verified in the running build.

---

## Asha (UX usability expert)

**Verdict: ACCEPT.**
**Q1 (confident <60s send, nothing by accident): YES.** The flow now reads top-to-bottom in the recipient's order (inbox stripe → opened email), the preview shows what will actually be sent, and the confirm gesture is fast but deliberate. **Q2 (UI tells the truth): YES.** Role chip is truthful on both pages, the dup warning survives the role switch, the preview no longer impersonates the subject line, and the armed state is announced to assistive tech.

Walked the trainee→sender promotion flow end-to-end: draft restored, "✓ Draft restored" status shown, dup banner re-fired for a URL sent earlier in the session. That was the scenario I most cared about.

**Remaining polish (explicitly non-blocking, for the real build):**
- Native `confirm()` on audit cancel — replace with an inline pattern when the audit page grows up.
- The inbox stripe could indicate combined subject+preheader truncation length per client (Gmail ~110 chars). Nice-to-have.
- Role change still reloads the page (now safely). A client-side role switch would be smoother.

## Jonah (editorial tools designer)

**Verdict: ACCEPT.**
**Q1: YES.** Hammered the send button across all three roles and both timing modes: one request per confirmed send, every time; armed state can't be left dangling (8s auto-disarm verified); past schedules blocked client- and server-side. **Q2: YES.** Audit log now answers who/what/when in local time, filterable by kind in one click, with segments recorded per entry. The no-URL warning follows you into the confirm prompt.

**Remaining polish (non-blocking, for the real build):**
- Segments are recorded but still not used for Braze targeting — the prototype's known scope cut; keep the "not in production" framing in the docs.
- In-memory stores still lose everything on restart — deferred since v1, still deferred.
- Real Braze test-send and schedule-cancellation remain mocked.

---

No blockers. Ship iter-03.
