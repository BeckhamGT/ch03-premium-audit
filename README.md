# Class Code and Premium Audit Assistant

Reusable first-pass payroll audit skill for Linden Shore Mutual. It classifies actual duties, allocates payroll and drafts employer confirmation questions. It does not set rates or quote premiums. Outputs are proposed allocations, separate from learner judgments and employer confirmation.

## Setup and commands

Requires Python 3.11+ and curl on PATH, with HTTPS access to the auditor-provided public Google Drive sources. No pip dependencies or secrets are needed for the audit runtime. Run from this repository root:

```sh
python3 skills/class-code-assistant/scripts/audit.py annapolis-courier
python3 skills/class-code-assistant/scripts/audit.py all
```

Single-employer output goes under its unique `artifacts/runs/<UTC-run-id>/deliverables/`; all-employer output goes to `deliverables/`. Use `--run-id <unique-name> --output <separate-path>` for comparison runs. Every command freshly lists the employer folders and downloads the current guide and employer files, retaining URL/hash provenance and snapshots. Retrieval failures or changed evidence stop calculation; there is no stale cache fallback. Existing outputs remain prior evidence until a new run succeeds.

Read [the skill](skills/class-code-assistant/SKILL.md), [rule map/design](docs/design.md), and [input contract](skills/class-code-assistant/references/input-contract.md). The reviewed facts describe duties and evidence, not expected totals; current source hashes bind them to the records reviewed. Changed sources require review before rebinding. Changed guide/interview rules require reviewing calculations too. Decimal money is rounded half-up per adjustment to cents; log/payment dates are filtered to inclusive audit periods.

## A new employer

1. Obtain its source locations from the auditor. Copy the source catalog and add a safe employer slug with `folder_url`.
2. Run `python3 skills/class-code-assistant/scripts/audit.py <new-slug> --catalog <catalog.json> --review-sources`.
3. Read all current sources. Create facts JSON following the input contract: inclusive period, every worker's actual duties and evidence filenames, supported work mode, guide/interview hashes, source hashes from that run manifest, and explicit open items. No payroll answers/totals are needed in facts. Do not infer duties from titles.
4. Run `python3 skills/class-code-assistant/scripts/audit.py <new-slug> --catalog <catalog.json> --facts <facts.json>`. It fetches again and rejects intervening evidence changes. Independently verify that employer; the supplied-six verification script is not a universal oracle.

Supported runtime inputs are public Drive UTF-8 CSV/Markdown in small folders with the documented schemas. Authenticated/native files and pagination require adapter work. Drive HTML inventory is a narrow adapter that may change. Supported modes cover reviewed field duties, office site days, roofing/siding/gutters, weekly dispatchers and restaurant/catering eligibility. Supported time-based catering splits above 40%, varying daily allowances, or excluded owners appearing on the register need additional reviewed normalization; retain uncertainty rather than force an unsupported case into a mode.

## Deliverables and evidence

- [Audit report](deliverables/audit-report.md): code comparisons, every worker/payment treatment, deciding records, reconciliation, open matters and call priorities.
- [Employer questions](deliverables/audit-questions.md): confirmation of each ledger treatment and each relied-on record.
- `deliverables/codes/*.csv`: six required CSVs with exact columns, cents, current guide paragraph identifiers and no zero rows.
- `deliverables/calculation-ledger.json`: worker/payment and dispatcher-week calculations.
- `interviews/ch03-premium-audit-20261102-1929.md`: original complete cumulative export, byte-matched to the original. Earlier exports are message prefixes; no extra session boundaries were invented from separate downloads.
- `artifacts/runs/learner-reviewed/`: current source snapshots, manifest, reviewed facts, learner-state snapshot and independent verification. Other named runs preserve the pre-review baseline, source review, genuine gutters-validation failure, recovery, real single-employer and repeat-run evidence.
- [Verification/handoff](docs/verification.md), [learner review](docs/learner-review.md), [presentation brief](docs/presentation-brief.md), and [Entire setup history](docs/setup.md).

## Verification

```sh
python3 -m unittest discover -s tests -v
python3 tests/independent_reconcile.py artifacts/runs/learner-reviewed deliverables
git diff --check
entire doctor
entire checkpoint explain HEAD --json
entire checkpoint explain HEAD --transcript > /tmp/insurance-candidate-capture.jsonl
```

Synthetic tests cover the 4/5 site-day, 14/15 roof-day, 1/2 weekly ride-day, USD47 allowance and 40% catering boundaries, missing/expired/mismatched certificates, duplicate days/payroll, period filtering, missing evidence, changed sources and unavailable sources. The independent supplied-record verifier imports no product business-rule functions, derives results using integer cents, and checks CSV schema, guide references and confirmation coverage. Real single/all commands and fresh repeat retrieval are recorded in the verification document.

Inspect the actual report and deciding records, then state your own acceptance/rejection of each employer's reported split and its supporting record in the captured coding chat. Keep Harbor's undefined governing-code treatment, Severn's certificate mismatch, Patuxent's travel evidence and Larkspur's exact sales period explicit. Silence is never approval.

Current review: all six individual choices and cited records are captured in `docs/learner-review.md`, including revised acceptance of the proposed corrections for Severn and Annapolis. Annapolis explicitly cites `weekly-payroll.csv` and `route-log.csv`. `docs/learner-review-state.json` preserves current displays only when guide/employer-source hashes match; earlier conflicting choices remain historical. CSVs retain company-rule calculations. See the verification handoff for remaining open-evidence and visual-QA limitations; no submission readiness is claimed.

## Interview rule

**Interview rule.** You conduct the stakeholder interview yourself, and the questions are yours. Do not connect a coding agent or any other AI to the interview to run, script, or automate it. The interview transcript is assessed together with the code; a project whose interview was run by an agent is not scored.

Plan for at most three conversations. Preserve one final complete original Markdown export per session under `interviews/` and commit it unchanged. Read employer sources/company rules from auditor-provided locations during every run. Keep the coding session captured. Commit required work and follow authorized synchronization to the existing fork; publishing is separate from submission and grading.
