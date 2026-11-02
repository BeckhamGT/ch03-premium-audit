"""Pure source-backed calculations. Reviewed duty facts are separate from payroll."""
import csv
import io
import re
import calendar
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

D = Decimal


def money(value):
    n = D(str(value))
    if not n.is_finite() or n < 0:
        raise ValueError('Money must be finite and nonnegative')
    return n.quantize(D('.01'), rounding=ROUND_HALF_UP)


def table(text):
    return list(csv.DictReader(io.StringIO(text)))


def period_rows(rows, start, end, key='date'):
    date.fromisoformat(start)
    date.fromisoformat(end)
    return [r for r in rows if start <= date.fromisoformat(r[key]).isoformat() <= end]


def unique_days(rows, worker, key='employee_id'):
    return len({r['date'] for r in rows if r.get(key) == worker})


def office_code(days, governing):
    if days < 5:
        return 'C-110', None
    if not governing:
        return 'C-110', 'No unique governing field code: provisional clerical retention; confirm treatment.'
    return governing, None


def roof_code(days):
    return 'R-310' if days >= 15 else 'R-320'


def dispatcher_code(days):
    return 'T-610' if days >= 2 else 'C-110'


def allowance(total, days):
    if days < 0 or int(days) != days:
        raise ValueError('Invalid travel day count')
    paid = money(total)
    excluded = min(paid, D(days) * 47)
    return paid - excluded, excluded


def certificate(name, certs, start, end, candidate=None):
    exact = [c for c in certs if c['subcontractor'] == name]
    valid = any(c['coverage_from'] <= start and c['coverage_to'] >= end for c in exact)
    if valid:
        return D('0'), None
    if candidate:
        return D('.60'), 'Certificate name mismatch unresolved; proposed uninsured inclusion pending identity and full-period coverage evidence.'
    return D('.60'), None


def catering_code(offsite, total, has_time_records=False):
    if total <= 0:
        return 'F-710', 'Gross receipts unavailable; provisional restaurant code requires confirmation.'
    if offsite / total < D('.40'):
        return 'F-710', None
    if not has_time_records:
        return 'F-710', 'Catering eligible but time allocation missing; provisional restaurant retention, never split by receipts.'
    return None, 'Use reviewed time-based code allocations; eligibility alone does not allocate wages.'


def analyze(files, facts, guide):
    start, end = facts['start'], facts['end']
    # A changed source is reviewed before these facts may be reused (enforced by CLI).
    codes = dict((code, para) for para, code in re.findall(r'\*\*(CG-\d+)\. ([A-Z]-\d+)', guide))
    payroll = table(files['payroll-register.csv'])
    ids = [p['employee_id'] for p in payroll]
    if len(set(ids)) != len(ids) or set(ids) != set(facts['workers']):
        raise ValueError('Duplicate payroll IDs or unreviewed employee roster')
    logs = period_rows(table(files.get('site-signin-log.csv', 'date,employee_id\n')), start, end)
    times = period_rows(table(files.get('crew-timesheets.csv', 'date,employee_id,work_type,hours\n')), start, end)
    routes = period_rows(table(files.get('route-log.csv', 'date,ride_along_id\n')), start, end)
    weekly = table(files.get('weekly-payroll.csv', 'week_start,week_end,employee_id,gross_pay\n'))
    if len({(w['employee_id'], w['week_start']) for w in weekly}) != len(weekly):
        raise ValueError('Duplicate weekly payroll entries')
    if any(not (start <= w['week_start'] <= w['week_end'] <= end) for w in weekly):
        raise ValueError('Payroll week crosses or lies outside audit period; review rather than prorate')
    if any(w['employee_id'] not in ids for w in weekly):
        raise ValueError('Unknown employee in weekly payroll')
    receipts = table(files.get('gross-receipts.csv', 'month,dine_in_receipts,offsite_catering_receipts\n'))
    receipts = [r for r in receipts if start[:7] <= r['month'] <= end[:7]]
    if len({r['month'] for r in receipts}) != len(receipts):
        raise ValueError('Duplicate monthly receipts')
    offsite = sum((money(r['offsite_catering_receipts']) for r in receipts), D(0))
    total_receipts = offsite + sum((money(r['dine_in_receipts']) for r in receipts), D(0))
    totals = defaultdict(lambda: D(0))
    ledger, opens, week_ledger = [], list(facts.get('open_items', [])), []
    base = sum((money(p['wages_paid']) for p in payroll), D(0))
    included_allowances = excluded_allowances = sub_added = D(0)

    def add(person, amount, code, reason, records, status='supported'):
        nonlocal totals
        if code not in codes:
            raise ValueError('Code absent from current guide: ' + str(code))
        amount = money(amount)
        totals[code] += amount
        ledger.append({'person': person, 'amount': str(amount), 'code': code,
                       'reason': reason, 'records': records, 'status': status})

    # Establish governing field payroll before applying the office exception.
    field = defaultdict(lambda: D(0))
    for p in payroll:
        f = facts['workers'][p['employee_id']]
        if f['mode'] == 'field':
            field[f['code']] += money(p['wages_paid'])
        elif f['mode'] == 'roof-siding':
            roof = [r for r in times if r['work_type'] == 'roofing' and D(r['hours']) > 0]
            field[roof_code(unique_days(roof, p['employee_id']))] += money(p['wages_paid'])
    highest = max(field.values(), default=D(0))
    leaders = [c for c, n in field.items() if n == highest]
    governing = leaders[0] if len(leaders) == 1 else None
    for p in payroll:
        worker = p['employee_id']
        f = facts['workers'][worker]
        mode = f['mode']
        wage = money(p['wages_paid'])
        refs = ['payroll-register.csv'] + f['records']
        issue = None
        if mode == 'field':
            code, why = f['code'], f['duty'] + '; CG-02/CG-05 actual duties'
        elif mode == 'office':
            count = unique_days(logs, worker)
            code, issue = office_code(count, governing)
            why = f'{count} distinct audit-period site days; governing={governing}; Nadia 01:59–02:00 PM'
            if 'site-signin-log.csv' not in files:
                issue = 'No site log supplied: office allocation is proposed from reviewed duties; owner must confirm whether site visits occurred.'
                why = 'Reviewed office duties; site-day count unverified because no site log was supplied; CG-04'
            refs += ['site-signin-log.csv'] if 'site-signin-log.csv' in files else []
        elif mode == 'roof-siding':
            person_times = [r for r in times if r['employee_id'] == worker]
            if not person_times or any(r['work_type'] not in ('roofing', 'siding', 'gutters') for r in person_times):
                raise ValueError('Missing or unreviewed mixed-work timesheet')
            count = unique_days([r for r in person_times if r['work_type'] == 'roofing' and D(r['hours']) > 0], worker)
            code, why = roof_code(count), f'{count} distinct roof days; whole-worker wage; Nadia 02:26/02:28 PM'
            refs += ['crew-timesheets.csv']
        elif mode == 'dispatcher':
            weeks = [w for w in weekly if w['employee_id'] == worker]
            if not weeks or sum((money(w['gross_pay']) for w in weeks), D(0)) != wage:
                raise ValueError('Weekly payroll does not reconcile to register')
            by_code = defaultdict(lambda: D(0))
            counts = defaultdict(int)
            for w in weeks:
                n = unique_days([r for r in routes if w['week_start'] <= r['date'] <= w['week_end']], worker, 'ride_along_id')
                c = dispatcher_code(n)
                by_code[c] += money(w['gross_pay']); counts[c] += 1
                week_ledger.append({**w, 'ride_days': n, 'code': c})
            for c, amt in by_code.items():
                add(p['name'], amt, c, f'{counts[c]} whole pay weeks; >=2 ride days T-610, otherwise C-110; Nadia 02:20 PM', refs + ['weekly-payroll.csv', 'route-log.csv'])
            if money(p.get('travel_allowance_paid', '0')):
                raise ValueError('Dispatcher allowance needs reviewed weekly allocation')
            continue
        elif mode == 'restaurant':
            code, issue = catering_code(offsite, total_receipts)
            last_day = calendar.monthrange(int(end[:4]), int(end[5:7]))[1]
            if start[-2:] != '01' or int(end[-2:]) != last_day or not receipts or receipts[-1]['month'] != end[:7]:
                issue = (issue + ' ' if issue else '') + 'Supplied monthly receipts do not establish exact audit-period receipts; allocation provisional pending owner confirmation.'
            why = f'Offsite receipts {offsite:.2f} / gross {total_receipts:.2f}; Nadia 02:21/02:28 PM; no sales-proportion split'
            refs += ['gross-receipts.csv']
        else:
            raise ValueError('Unreviewed worker mode: ' + mode)
        if issue:
            opens.append(p['name'] + ': ' + issue + f' Wage affected: USD {wage:.2f}.')
        add(p['name'], wage, code, why, refs, 'proposed/open' if issue else 'supported')
        if 'travel_allowance_paid' in p:
            inc, exc = allowance(p['travel_allowance_paid'], int(p['travel_days']))
            included_allowances += inc; excluded_allowances += exc
            if money(p['travel_allowance_paid']):
                add(p['name'] + ' — allowance', inc, code,
                    f'Paid {money(p["travel_allowance_paid"]):.2f}; {p["travel_days"]} recorded travel days × USD 47; excluded {exc:.2f}; included {inc:.2f}; CG-03/Nadia 02:17–02:18 PM', refs,
                    'proposed/open' if int(p['travel_days']) == 0 else 'supported; travel-day evidence confirmation')
                if int(p['travel_days']) == 0:
                    opens.append(p['name'] + f': USD {inc:.2f} allowance with zero recorded travel days; proposed full inclusion; owner must explain payment or supply substantiation.')
    payments = period_rows(table(files.get('subcontractor-payments.csv', 'date,subcontractor,work,invoice,amount_paid\n')), start, end)
    if len({r['invoice'] for r in payments}) != len(payments):
        raise ValueError('Duplicate subcontractor invoice')
    certs = table(files.get('insurance-certificates.csv', 'subcontractor,coverage_from,coverage_to\n'))
    for p in payments:
        work = facts['subcontract_work'][p['work']]
        candidate = facts.get('certificate_candidates', {}).get(p['subcontractor'])
        fraction, issue = certificate(p['subcontractor'], certs, start, end, candidate)
        amount = money(money(p['amount_paid']) * fraction)
        sub_added += amount
        reason = f'{p["invoice"]} paid {p["amount_paid"]} on {p["date"]}; full-period certificate test; inclusion {fraction * 100}% = {amount:.2f}; CG-06/Nadia 02:20 PM'
        if candidate:
            reason += '; candidate certificate: ' + candidate
            for c in certs:
                if c['subcontractor'] == candidate:
                    coverage = 'full-period dates; identity unresolved' if c['coverage_from'] <= start and c['coverage_to'] >= end else 'not full audit period'
                    reason += f'; coverage {c["coverage_from"]} through {c["coverage_to"]} ({coverage})'
        add(p['subcontractor'], amount, work, reason, ['subcontractor-payments.csv', 'insurance-certificates.csv'], 'proposed/open' if issue else 'supported')
        if issue:
            opens.append(p['subcontractor'] + ': ' + issue + f' Invoice {p["invoice"]}: proposed addition USD {amount:.2f}.')
    reported = {}
    for c, amount in re.findall(r'\|\s*([A-Z]-\d+)\s*\|\s*\d+\s*\|\s*([\d.]+)\s*\|', files['application.md']):
        if c in reported:
            raise ValueError('Duplicate reported code')
        reported[c] = money(amount)
    if not reported:
        raise ValueError('Application split not found')
    allocated = sum(totals.values(), D(0))
    if allocated != base + included_allowances + sub_added:
        raise AssertionError('Payroll reconciliation failed')
    for item in ledger:
        item['records'] = sorted(set(item['records']))
        if any(r not in files for r in item['records']):
            raise ValueError('Evidence record missing')
    return {'name': facts['name'], 'start': start, 'end': end, 'totals': dict(totals),
            'reported': reported, 'codes': codes, 'base': base,
            'allowance_included': included_allowances, 'allowance_excluded': excluded_allowances,
            'subcontract_added': sub_added, 'allocated': allocated, 'ledger': ledger,
            'open_items': sorted(set(opens)), 'weekly': week_ledger,
            'governing': governing, 'source_names': sorted(files),
            'call_reason': facts.get('call_reason', ''), 'priority': facts.get('priority', 99)}
