# Implementation plan and authority

Build a Python 3.11+ standard-library CLI and an agent skill. The skill reviews actual duties and open cases, binds reviewed facts to current source hashes, then runs decimal calculations. Facts contain classifications supported by duties, not expected payroll totals. New employers use the same facts schema and calculations.

Every operational run re-lists public auditor-provided Drive folders and downloads the guide and employer files. Preserve textual source bytes, hashes, URLs, retrieval UTC times and inventory in a unique run directory. Public Drive HTML inventory is an adapter, not a stable API: fail closed on an unrecognized response or incomplete inventory. No stale fallback. Connected Drive tools established the initial inventory independently. No credentials are used.

Money uses Decimal with half-up cents per monetary adjustment; this is a documented technical rounding convention, not an interview claim. Dates use inclusive employer audit periods, and dispatcher weeks use supplied week_start/week_end. Distinct worker/date pairs prevent duplicate logs inflating thresholds; duplicate payroll/payment rows fail for review. Partial payroll periods and unknown governing codes require explicit uncertainty.

Stage output content after full calculation; leave prior deliverables untouched on source or calculation failure and write a failed-run status. Publication uses a filesystem copy, so an I/O failure during publication requires inspecting the output rather than assuming a successful complete update. CSVs are proposed first-pass allocations, not approval. Reports include each worker, subcontract payment, record, adjustment and confirmation question, with open matters and potential consequences. Preserve learner judgments as pending until supplied in the captured chat.

## Source-to-rule-to-verification map

| Authority | Rule and scope | Verification |
|---|---|---|
| CG-02; Nadia 01:53 PM, 02:22 PM | Actual duties; reviewed duty facts rather than title inference | Worker ledger and source references |
| CG-04; Nadia 01:59–02:00 PM | Office worker <=4 site days clerical; >=5 whole pay governing field code (most field payroll) | 4/5 boundary; Harbor no-governing-code uncertainty |
| CG-07, CG-11/12; Nadia 02:26, 02:28 PM | Roofing/siding contractors: >=15 audit-period roof days whole wage R-310, otherwise R-320 | 14/15 boundary, unique dates, period filter |
| CG-04/31, CG-07; Nadia 02:20 PM | Dispatcher >=2 ride days per pay week entire week T-610; <=1 C-110 | 1/2 boundary and weekly/annual reconciliation |
| CG-03; Nadia 02:17–02:18 PM | Out-of-town daily allowance exclusion <=47/day supported by actual travel days; excess included | 47 limit, zero-day unsupported allowance |
| CG-06; Nadia 02:20 PM | No certificate for full audit period: 60% of payments, lapsed certificate treated absent; name mismatch unresolved | Missing/expired and name-mismatch tests |
| CG-41/42, CG-07; Nadia 02:21, 02:28 PM | Catering >=40% gross receipts eligible; below all crew F-710; never sales-proportion payroll split | 40% boundary; missing time records uncertainty |
| CG-05 | Excluded owners omitted; included owners classified by actual work | Included owner wiring and exclusion records |
| Nadia 02:00–02:03, 02:22 PM | Records decide over application/memory; undefined cases proposed with reasons and employer confirmation | Reports distinguish facts, proposals, open questions |
| Assignment deliverables | Six CSVs, report, questions, reusable skill, instructions, original export, real capture | Schema checks, independent original-record derivation, operational runs |

Guide: July 2025 edition, URL in source catalog. Interview timestamps are the export's displayed local times on November 2, 2026; no separate session IDs or timezone are supplied. Earlier exports have identical message prefixes; keep only the latest final cumulative export. Its SHA-256 is dcf713c98c965e9e8b176b1b0d5ed94f62ce51594fbe36585934473cdc815693.

The shared playbook contains Project D lessons; no Project E-specific section was present when read. Apply its general missing-evidence and truthful-status requirements without inventing historical details. Historical projects remain untouched.
