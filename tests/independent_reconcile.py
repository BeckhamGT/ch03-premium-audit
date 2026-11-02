"""Supplied-record evidence check; deliberately imports no product calculations.

This verifier derives expectations from original CSVs and separately transcribed
source rules, using integer cents. Employer-specific cases belong in verification,
not the reusable calculator. Usage: python3 tests/independent_reconcile.py RUN_DIR OUTPUT_DIR
"""
import csv
import json
import re
import sys
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

run, output = map(Path, sys.argv[1:])
root = run / 'sources'
ledger = json.loads((output / 'calculation-ledger.json').read_text())


def cents(s):
    return int((Decimal(s) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def read(e, name):
    return list(csv.DictReader((root / e / name).open()))


evidence = []
for e in sorted(ledger):
    pay = read(e, 'payroll-register.csv')
    start, end = '2025-07-07', '2026-07-05'
    sums = defaultdict(int)
    base = sum(cents(r['wages_paid']) for r in pay)
    additions, exclusions = 0, 0
    details = []
    for p in pay:
        worker, n = p['employee_id'], cents(p['wages_paid'])
        if e == 'harbor-point-legal':
            code = 'C-110'  # provisional: no governing field payroll; not a new policy
        elif e == 'bay-crest-exteriors':
            if worker in {'BC-E09', 'BC-E10'}:
                code = 'R-310' if worker == 'BC-E09' else 'C-110'
            else:
                roof_dates = {r['date'] for r in read(e, 'crew-timesheets.csv') if r['employee_id'] == worker and r['work_type'] == 'roofing' and Decimal(r['hours']) > 0 and start <= r['date'] <= end}
                code = 'R-310' if len(roof_dates) >= 15 else 'R-320'
                details.append(f'{worker}: {len(roof_dates)} roof days')
        elif e == 'severn-homebuilders':
            code = 'C-110' if worker in {'SH-E06', 'SH-E08'} else 'H-420'
        elif e == 'patuxent-electric':
            code = 'C-110' if worker == 'PE-E07' else 'E-510'
            paid = cents(p['travel_allowance_paid'])
            excluded = min(paid, int(p['travel_days']) * 4700)
            extra = paid - excluded
            sums[code] += extra; additions += extra; exclusions += excluded
            if paid:
                details.append(f'{p["name"]}: allowance {paid/100:.2f}, excluded {excluded/100:.2f}, included {extra/100:.2f}')
        elif e == 'annapolis-courier':
            if worker in {'AC-E04', 'AC-E05'}:
                weeks = [w for w in read(e, 'weekly-payroll.csv') if w['employee_id'] == worker]
                assert sum(cents(w['gross_pay']) for w in weeks) == n
                code_counts = defaultdict(int)
                for w in weeks:
                    dates = {r['date'] for r in read(e, 'route-log.csv') if r['ride_along_id'] == worker and w['week_start'] <= r['date'] <= w['week_end']}
                    code = 'T-610' if len(dates) >= 2 else 'C-110'
                    sums[code] += cents(w['gross_pay']); code_counts[code] += 1
                details.append(f'{p["name"]}: {dict(code_counts)} weeks')
                continue
            code = 'C-110' if worker == 'AC-E06' else 'T-610'
        elif e == 'larkspur-lane-bistro':
            receipts = read(e, 'gross-receipts.csv')
            off = sum(cents(r['offsite_catering_receipts']) for r in receipts)
            gross = off + sum(cents(r['dine_in_receipts']) for r in receipts)
            assert off * 100 < gross * 40
            code = 'F-710'
            if not details:
                details.append(f'Supplied calendar sales: catering {off/100:.2f}, total {gross/100:.2f}, share {off/gross:.8%}; exact audit-period evidence open')
        else:
            raise AssertionError('Independent derivation not established for this employer')
        sums[code] += n
    if e in {'bay-crest-exteriors', 'severn-homebuilders', 'harbor-point-legal'}:
        sites = read(e, 'site-signin-log.csv')
        for p in pay:
            n = len({r['date'] for r in sites if r['employee_id'] == p['employee_id'] and start <= r['date'] <= end})
            if n:
                details.append(f'{p["name"]}: {n} distinct site days, wage {p["wages_paid"]}')
    if e == 'severn-homebuilders':
        for p in read(e, 'subcontractor-payments.csv'):
            # Original certificates: Tenbury fully covered; Tidewater absent;
            # Kent candidate differs by name AND lapses 2026-01-31.
            if p['subcontractor'] == 'Tenbury Ridge Framing Co.':
                extra = 0
            else:
                extra = int((Decimal(p['amount_paid']) * Decimal('60')).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
            code = 'R-310' if p['work'] == 'roofing' else 'H-420'
            sums[code] += extra; additions += extra
            details.append(f'{p["invoice"]}: payment {p["amount_paid"]}, payroll addition {extra/100:.2f}')
    actual_rows = read_output = list(csv.DictReader((output / 'codes' / (e + '.csv')).open()))
    assert list(actual_rows[0]) == ['class_code', 'payroll_allocated', 'rationale_ref']
    assert len({r['class_code'] for r in actual_rows}) == len(actual_rows)
    actual = {r['class_code']: cents(r['payroll_allocated']) for r in actual_rows}
    expected = {k: v for k, v in sums.items() if v}
    assert actual == expected, (e, actual, expected)
    assert sum(actual.values()) == base + additions
    paragraphs = dict((code, para) for para, code in re.findall(r'\*\*(CG-\d+)\. ([A-Z]-\d+)', (root / 'classification-guide.md').read_text()))
    for r in actual_rows:
        assert r['rationale_ref'] == paragraphs[r['class_code']]
        assert re.fullmatch(r'\d+\.\d{2}', r['payroll_allocated']) and cents(r['payroll_allocated']) > 0
    report = (output / 'audit-report.md').read_text()
    questions = (output / 'audit-questions.md').read_text()
    for i, row in enumerate(ledger[e]['ledger'], 1):
        assert f'{e}-A{i:02}' in report and f'{e}-A{i:02}' in questions
        assert row['person'] in report and row['person'] in questions
    for i, name in enumerate(ledger[e]['source_names'], 1):
        assert f'{e}-R{i:02}' in questions and name in report
    evidence += [f'## {ledger[e]["name"]}', '', f'Independent expected cents by code: `{expected}`.', '',
                 f'Base USD {base/100:.2f} + additions USD {additions/100:.2f} = allocated USD {sum(actual.values())/100:.2f}; allowances excluded USD {exclusions/100:.2f}. All CSV amounts and guide paragraph references match.', '']
    evidence += ['- ' + d for d in details] + ['']

(run / 'independent-verification.md').write_text('# Independent supplied-record reconciliation\n\nNo product business-rule functions imported. Integer-cent derivation from original run CSVs. Proposed treatment limits remain as reported.\n\n' + '\n'.join(evidence))
print('PASS: independently reconciled', len(ledger), 'employers, CSV schema, guide references, adjustment questions and source questions')
