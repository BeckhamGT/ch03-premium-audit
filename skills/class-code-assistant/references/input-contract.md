# Reviewed facts and source contract

The standard runtime is Python 3.11+ and curl; no pip dependencies or API secrets. The adapter supports public downloadable UTF-8 CSV/Markdown files in small Drive folders. Authenticated-only sources, native Google files, pagination, unexpected file types and layouts require an adapter update or explicit connector-assisted review; they fail instead of using old sources.

`sources.json` contains `guide_url`, `employer_root`, and `employers: {slug: {folder_url}}`. Employer slugs and filenames must be safe lowercase path names. The calculator does not discover duties from employer names.

`reviewed-facts.json` contains `guide_sha256`, `interview_sha256`, and `employers`. Each employer has `name`, inclusive ISO `start`/`end`, `workers` keyed by payroll `employee_id`, and `source_hashes` keyed by filename. Each worker has `mode`, a factual `duty` description, and deciding `records` filenames. Supported modes:

- `field`: a reviewed `code` for actual duties, including included owners. General non-crew occupations can use any current guide code supported by evidence.
- `office`: site-day rule with governing field code derived before moving office wages. Missing/tied governing code is an explicit proposed C-110 retention and open item.
- `roof-siding`: only mixed roofing, siding and gutter crews; unique positive-hour roof dates determine whole-worker pay.
- `dispatcher`: only dispatchers; unique ride dates within each supplied pay week determine that entire week's code. Weekly pay must equal register wages.
- `restaurant`: restaurant/catering crew. Supplied receipts determine eligibility only; no wage allocation by receipts. At/above 40% with missing time allocation, provisional restaurant retention remains open. A supported time-based split above threshold requires extending the reviewed normalization/calculator; the current CLI does not silently invent one.

Optional employer keys: `subcontract_work` maps documented trade to guide code; `certificate_candidates` identifies a possible differently named certificate, explicitly unresolved; `open_items` carries record-specific uncertainty; `priority`/`call_reason` holds a reviewed, evidence-based recommendation. These are facts and review judgments, not payroll answer totals. Pending learner decisions belong in the captured chat, not this configuration.

Payroll CSV requires `employee_id,name,wages_paid`; extra position text is informational. Optional travel columns are `travel_days,travel_allowance_paid`, separately paid from wages. The aggregate daily-cap calculation is appropriate to documented flat daily allowances; varying daily amounts require daily normalization before use. Supplied payroll day counts and field notes support a proposal, but owner-confirmed daily travel evidence is still requested.

Other supported CSVs use the supplied headers: site log (`date,employee_id`), crew times (`date,employee_id,work_type,hours`), weekly payroll (`week_start,week_end,employee_id,gross_pay`), routes (`date,ride_along_id`), receipts (`month,dine_in_receipts,offsite_catering_receipts`), subcontract payments (`date,subcontractor,work,invoice,amount_paid`), certificates (`subcontractor,coverage_from,coverage_to`). Application Markdown contains rows `| CODE | headcount | amount |`.

All money must be finite nonnegative decimal USD. All log/payment dates are ISO and filtered to the audit period; repeated day entries count once. Weekly payroll extending beyond the period fails rather than prorating. Register wages must represent the stated audit period; owner exclusions not already reflected in the register need explicit normalization and reconciliation. Unknown work, governing ties, name mismatches and missing evidence remain review matters. Monthly receipts crossing audit boundaries are not silently prorated: flag the mismatch and request exact-period records.

For changed/new sources, first use `--review-sources`, read the snapshots, establish these facts from duties and governing sources, then copy each reviewed file hash from that run manifest. Rerun the ordinary command, which re-fetches sources and rejects any intervening change. Never update hashes mechanically to suppress a review failure.
