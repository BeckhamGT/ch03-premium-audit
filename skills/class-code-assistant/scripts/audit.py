#!/usr/bin/env python3
"""Fresh-source premium payroll audit CLI. No rates, premiums, or approvals."""
import argparse
import csv
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from engine import D, analyze
from sources import collect, sha

SKILL = Path(__file__).resolve().parents[1]
ROOT = SKILL.parents[1]


def validate_binding(facts, guide, inputs, manifest):
    if sha(guide.encode()) != facts['guide_sha256']:
        raise ValueError('Guide changed: review rules and rebind facts before calculation')
    for employer in inputs:
        actual = {r['path'].split('/')[-1]: r['sha256'] for r in manifest['files']
                  if r['path'].startswith(employer + '/') and not r['path'].endswith('inventory.json')}
        if actual != facts['employers'][employer]['source_hashes']:
            raise ValueError(employer + ': source/inventory changed; review duties and rebind facts')


def render(results, out, source_root):
    out.mkdir(parents=True, exist_ok=False)
    (out / 'codes').mkdir()
    report = ['# Premium audit: proposed allocations', '',
              'First-pass review only. Learner decisions and employer confirmations are pending. No rates or premium calculations.', '',
              'Authority: July 2025 company guide and the preserved November 2, 2026 interview. Source-specific practices specialize CG-07; they are not universal wage-splitting rules.', '',
              '## Call first', '']
    for e, r in sorted(results.items(), key=lambda p: p[1]['priority'])[:2]:
        if r['call_reason']:
            report.append(f'- **{r["name"]}**: {r["call_reason"]}')
    report += ['', 'Priority is an auditor-call recommendation based on payroll discrepancies and unresolved evidence, not a premium-impact ranking.', '']
    questions = ['# Employer confirmation questions', '',
                 'Nadia puts these questions to each employer owner before sign-off. These are not stakeholder interview questions. Open policy interpretations also require Nadia review.', '']
    for e, r in sorted(results.items()):
        with (out / 'codes' / (e + '.csv')).open('w', newline='') as f:
            w = csv.writer(f, lineterminator='\n')
            w.writerow(['class_code', 'payroll_allocated', 'rationale_ref'])
            for code, n in sorted(r['totals'].items()):
                if n:
                    w.writerow([code, f'{n:.2f}', r['codes'][code]])
        rel = Path(os.path.relpath(source_root / e, out)).as_posix()
        link = lambda name: f'[{name}]({rel}/{name})'
        report += [f'## {r["name"]}', '', f'Audit period: {r["start"]} through {r["end"]}, inclusive. Learner review: **pending**.', '',
                   '| Code | Employer reported USD | Proposed USD | Difference USD | Guide |',
                   '|---|---:|---:|---:|---|']
        for c in sorted(set(r['reported']) | set(r['totals'])):
            old, new = r['reported'].get(c, D(0)), r['totals'].get(c, D(0))
            report.append(f'| {c} | {old:.2f} | {new:.2f} | {new-old:+.2f} | {r["codes"].get(c,"unrecognized")} |')
        report += ['', f'Reconciliation: base wages **USD {r["base"]:.2f}** + included allowances **USD {r["allowance_included"]:.2f}** + subcontractor additions **USD {r["subcontract_added"]:.2f}** = allocated **USD {r["allocated"]:.2f}**. Separately paid allowances excluded: **USD {r["allowance_excluded"]:.2f}**. Reclassifications move wages between codes without changing this total.', '',
                   '### Worker and payment detail', '',
                   'Each entry states the whole wage or payment adjustment, its deciding records, and the confirmation question ID. The application identifies aggregate codes; where it does not identify individual assignments, no individual reported code is invented.', '']
        questions += [f'## {r["name"]}', '']
        for i, row in enumerate(r['ledger'], 1):
            qid = f'{e}-A{i:02}'
            records = ', '.join(link(n) for n in row['records'])
            report += [f'- **{row["person"]}: USD {row["amount"]} → {row["code"]}** ({row["status"]}; {qid}). {row["reason"]}. Records: {records}.']
            questions += [f'- **{qid}** — Please confirm {row["person"]}: USD {row["amount"]} allocated/added to {row["code"]}, including this treatment: {row["reason"]}. Do {", ".join(row["records"])} support it, and are corrections needed?', '']
        report += ['', '### Open confirmation items', '']
        if not r['open_items']:
            report += ['No additional undefined treatment identified; all listed records and adjustments still await employer confirmation.', '']
        for i, item in enumerate(r['open_items'], 1):
            report += [f'- **Open {i}; owner: employer owner, reviewed by Nadia.** {item}']
            questions += [f'- **{e}-O{i:02}** — Please resolve and supply supporting records: {item}', '']
        report += ['', '### Record inventory and review', '']
        for i, name in enumerate(r['source_names'], 1):
            report += [f'- {link(name)} (confirmation {e}-R{i:02}).']
            questions += [f'- **{e}-R{i:02}** — Please confirm {name} is complete for {r["start"]} through {r["end"]}, including applicable owner elections, recorded duties, dates and amounts; identify corrections to the application or field notes.', '']
        report += ['', 'Learner review guide: compare the application with the code table, inspect the linked deciding records and open items, then state your own acceptance or rejection of the employer split and the record supporting that judgment in the captured coding chat.', '']
    (out / 'audit-report.md').write_text('\n'.join(report).rstrip() + '\n')
    (out / 'audit-questions.md').write_text('\n'.join(questions).rstrip() + '\n')
    (out / 'calculation-ledger.json').write_text(json.dumps(results, indent=2, default=str) + '\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('employer', help='employer slug in catalog, or all')
    parser.add_argument('--catalog', type=Path, default=SKILL / 'references/sources.json')
    parser.add_argument('--facts', type=Path, default=SKILL / 'references/reviewed-facts.json')
    parser.add_argument('--run-id', default=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    parser.add_argument('--output', type=Path, help='default: deliverables for all, run-local for one')
    parser.add_argument('--review-sources', action='store_true', help='retrieve only; review and bind facts before calculation')
    args = parser.parse_args(argv)
    if not args.run_id or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in args.run_id):
        parser.error('run-id must be a safe unique filename')
    run = ROOT / 'artifacts/runs' / args.run_id
    run.mkdir(parents=True, exist_ok=False)
    try:
        catalog = json.loads(args.catalog.read_text())
        selected = sorted(catalog['employers']) if args.employer == 'all' else [args.employer]
        if any(not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', e) for e in selected):
            raise ValueError('Unsafe employer slug')
        guide, inputs, manifest = collect(catalog, selected, run)
        if args.review_sources:
            (run / 'status.json').write_text(json.dumps({'state': 'sources-retrieved-needs-review'}) + '\n')
            print(run)
            return 0
        facts = json.loads(args.facts.read_text())
        validate_binding(facts, guide, inputs, manifest)
        transcript = ROOT / 'interviews/ch03-premium-audit-20261102-1929.md'
        if sha(transcript.read_bytes()) != facts['interview_sha256']:
            raise ValueError('Interview changed; review house practices')
        shutil.copyfile(args.facts, run / 'reviewed-facts.json')
        results = {e: analyze(inputs[e], facts['employers'][e], guide) for e in selected}
        output = args.output or (ROOT / 'deliverables' if args.employer == 'all' else run / 'deliverables')
        # Render links for final destination; write all staged content before publishing.
        staged = run / 'staged'
        render(results, staged, run / 'sources')
        for name in ('audit-report.md', 'audit-questions.md'):
            text = (staged / name).read_text()
            old = os.path.relpath(run / 'sources', staged)
            new = os.path.relpath(run / 'sources', output)
            (staged / name).write_text(text.replace(old + '/', new + '/'))
        shutil.copytree(staged, output, dirs_exist_ok=True)
        shutil.rmtree(staged)
        (run / 'status.json').write_text(json.dumps({'state': 'generated-pending-review', 'output': str(output), 'employers': selected}, indent=2) + '\n')
        print(json.dumps({'run': str(run), 'output': str(output), 'totals': {e: str(r['allocated']) for e, r in results.items()}}, indent=2))
        return 0
    except Exception as exc:
        (run / 'status.json').write_text(json.dumps({'state': 'failed-no-new-calculation-output', 'error': str(exc)}, indent=2) + '\n')
        print('Audit stopped: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
