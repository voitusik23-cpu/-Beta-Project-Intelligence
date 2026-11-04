# UI redesign and data visibility — 2026-11-04

## Scope and safety
Updated the existing Beta Project Intelligence application on `codex/finish-ui-20261102`. No second project was created. The visual audit and smoke checks used a copy of the local SQLite database. The original DB SHA-256 before and after was `AD360E998F75465FA92023519E9F45F489450603B97D8ECBFEA9944798A44C72`; environment files and user data were not changed.

## Findings: actual data vs earlier report
The local DB snapshot contains 386 projects, 668 project/source associations, 67 registered source rows, and 641 project events. Review statuses are 361 REJECTED, 19 REVIEW, and 6 PENDING. The review queue contains 24 records. The radar is a curated active subset and may include an already completed REVIEW dossier. Source status snapshot: 3 ACTIVE, one enabled ERROR, and remaining entries in NEEDS VALIDATION, API REQUIRED, DISABLED, ACCESS REQUIRED, or MANUAL.

The historical initial run completed 291 projects on 2026-11-02. The 26 cards and 12-source figure also came from that earlier report and do not represent current registry totals. The original UI intentionally excludes REJECTED/LATER records from active radar lists; these records remain in SQLite and are accessible via archive/rejected and dossier sections. Thus the historical totals and active-feed count were conflated in the earlier report, not evidence that records were deleted. No count was fabricated and scoring/selection criteria were not changed as part of this UI task.

## Changes
- `app/static/style.css`, `app/static/index.html`, `app/static/app.js`: unified dark graphite/blue theme, brighter layered panels, lime primary accent, local Inter Variable font, responsive sidebar/cards/controls, readable hierarchy, accessible focus and status announcements, counts for navigation, and category/stage/review filters plus name sorting.
- `app/main.py`: added offset pagination to `/api/projects`; `tests/test_api.py` covers retrieval across pages. Client loads successive 500-item pages to avoid silently truncating larger datasets.
- Dashboard labels now describe dossier/source-link/active-source counts precisely and distinguish registered from active source entries. Existing views, search, source collection, exports, review actions and language switch remain available.
- Bundled local Inter Variable WOFF2 font subsets and OFL notice under `app/static/fonts/`, removing dependence on a remote font request.
- Updated README, project rules, master task, roadmap, worklog and architecture baseline to reflect the actual code/data state and current implementation.

## Verification
Commands (run from repository root):

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m compileall -q app tools tests
node --check app/static/app.js
```

Final verification:
- `.venv\Scripts\python.exe -m unittest discover -s tests -v` — 13 passed (46.858 sec).
- `.venv\Scripts\python.exe -m compileall -q app tools tests` — passed.
- `node --check app/static/app.js` — passed.
- Local API smoke check on the isolated database: health reports 386 projects, 3 active sources, 0 qualifying top projects; pagination returned 200 + 186 records, total 386.
- `git diff --check` — passed.

Manual visual review: before/after dashboard viewed at approximately 1265×720 on an isolated local copy. Verified 386 dossier count, 24 queued, 361 rejected, 668 links, 3 active / 67 registered sources, non-empty event feed, two-column filters without clipping, and archive navigation showing all 361 retained records. The first visual pass exposed a queue hint that counted one completed review; it was corrected to match the queue badge. No screenshot with actual project data is committed to this public repository. Responsive CSS covers tablet/mobile widths; mobile browser capture was not available during this review.

## Remaining limitations
- Three sources are ACTIVE; one enabled connector currently reports ERROR; other registry records are not active integrations. No source health was re-labelled to make it appear connected.
- My Recommendations remains empty under the current existing verification requirements. Scoring and thresholds were not changed.
- `app/screening.py` contains a pre-existing/unapproved working-tree diff that changes evidence-confidence behavior. It is deliberately excluded from this UI commit; do not merge it without separate review/approval.
- This repository has no frontend bundler/build manifest. Python tests/compile and Node syntax check are the available code checks.
