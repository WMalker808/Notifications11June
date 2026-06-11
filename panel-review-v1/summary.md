# Panel review v1 — summary

## Outcome
ACCEPT after **2 iterations**. Both panellists (Priya, UX; Tom, editorial) signed off on iter-02.

## Stakeholder requirements addressed (MVP)
| Theme | Votes | In MVP |
|---|---|---|
| Preview & testing | 7 | ✅ Preheader rendered, image swap + "use article image", 🧪 Send-test button in dashed amber mini-card |
| Access control | 4 | ✅ Sender / Trainee / Viewer role chip in sidebar; Trainee = dry-run; Viewer = read-only |
| Tracking & monitoring | 4 | ✅ In-memory audit log at `/audit`, UTM params auto-appended, kind chips + substring filter |
| Subject line customisation | 3 | ✅ 200-char subject, editable/removable "Breaking news:" prefix, preheader field |
| Schedule / intelligent timing | 3 | ✅ Intelligent removed; pending schedules listed on `/audit` with named cancel-confirm |
| Duplicate detection | 2 | ✅ Non-blocking banner on URL paste; "earlier today" / "yesterday" wording |
| Simpler interface | 2 | ✅ Single page, no tabs, fields ordered to match mental model |

## Deferred (noted, not built)
Performance benchmarks, dependency review, 24/7 support, training process, backup plan, Braze T&Cs, Braze session mgmt, Composer integration, opt-out category UI, live-blog block selector, send-corrections mode, real Braze test-send, real Braze schedule cancellation, persistence across server restarts.

## Iteration log
| Iter | Verdict | Headline issues |
|---|---|---|
| 01 | REJECT | Field order wrong; subject/headline ambiguous; Send vs Send-test stacked & visually identical; Trainee role = Viewer; `hasSegment = true` hard-coded bug; "Braze" leaked into UI copy. |
| 02 | **ACCEPT** | All iter-01 blockers fixed. Nits only (role-chip chevron, opened-vs-inbox preview, draft-loss on role change, raw ISO in cancel-confirm). |

## Outstanding nits (future polish)
- Role chip needs a visible ▾ to signal it's clickable.
- Email preview mocks the *opened* email; an "inbox preview" stripe above would close the loop on why subject + preheader matter.
- Image field is paste-URL only — no thumbnail next to input (right-rail preview covers it).
- Role change is a full page reload — loses in-progress draft.
- Cancel-confirm shows raw UTC ISO; a localised time would be friendlier.
- Audit filter is substring across row text — a kind-pill toggle would be cleaner.

## Artefacts
- `panel-review-v1/iter-01-changes.md` — builder log
- `panel-review-v1/iter-01-feedback.md` — Priya + Tom feedback (REJECT)
- `panel-review-v1/iter-02-changes.md` — builder log
- `panel-review-v1/iter-02-feedback.md` — Priya + Tom feedback (ACCEPT)
