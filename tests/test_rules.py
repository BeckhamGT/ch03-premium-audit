"""Synthetic boundary and failure probes, separate from real-employer reconciliation."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/class-code-assistant/scripts'))
from engine import (D, analyze, allowance, catering_code, certificate, dispatcher_code,
                    office_code, period_rows, roof_code, unique_days)
from sources import collect, inventory
from audit import main, validate_binding


class Rules(unittest.TestCase):
    def test_source_change_requires_review(self):
        from sources import sha
        facts = {'guide_sha256': sha(b'guide'), 'employers': {'new-employer': {'source_hashes': {'payroll.csv': 'old'}}}}
        with self.assertRaisesRegex(ValueError, 'source/inventory changed'):
            validate_binding(facts, 'guide', {'new-employer': {}}, {'files': [{'path': 'new-employer/payroll.csv', 'sha256': 'new'}]})

    @patch('audit.collect', side_effect=RuntimeError('synthetic source unavailable'))
    def test_cli_failure_preserves_output(self, collect):
        with tempfile.TemporaryDirectory() as t, patch('audit.ROOT', Path(t)):
            out = Path(t) / 'deliverables'
            out.mkdir(); (out / 'audit-report.md').write_text('prior result')
            self.assertEqual(main(['all', '--run-id', 'synthetic-failure', '--output', str(out)]), 1)
            self.assertEqual((out / 'audit-report.md').read_text(), 'prior result')
            self.assertIn('failed', (Path(t) / 'artifacts/runs/synthetic-failure/status.json').read_text())

    def test_missing_site_evidence_and_duplicate_weeks(self):
        files = {'payroll-register.csv': 'employee_id,name,wages_paid\nX,A,100.00\n',
                 'application.md': '| C-110 | 1 | 100.00 |'}
        facts = {'name': 'Synthetic', 'start': '2025-07-07', 'end': '2026-07-05',
                 'workers': {'X': {'mode': 'office', 'records': []}}}
        result = analyze(files, facts, '**CG-04. C-110 Office**')
        self.assertIn('No site log', result['open_items'][0])
        files['weekly-payroll.csv'] = 'week_start,week_end,employee_id,gross_pay\n' + '2025-07-07,2025-07-13,X,50.00\n' * 2
        with self.assertRaisesRegex(ValueError, 'Duplicate weekly'):
            analyze(files, facts, '')

    def test_whole_worker_gutters_and_duplicate_payroll(self):
        files = {'payroll-register.csv': 'employee_id,name,wages_paid\nX,A,100.00\n',
                 'crew-timesheets.csv': 'date,employee_id,work_type,hours\n2025-07-07,X,gutters,8\n',
                 'application.md': '| R-320 | 1 | 100.00 |'}
        facts = {'name': 'Synthetic', 'start': '2025-07-07', 'end': '2026-07-05',
                 'workers': {'X': {'mode': 'roof-siding', 'records': []}}}
        result = analyze(files, facts, '**CG-11. R-310 Roofing**\n**CG-12. R-320 Siding and gutters**')
        self.assertEqual(result['totals'], {'R-320': D('100.00')})
        files['payroll-register.csv'] += 'X,A,100.00\n'
        with self.assertRaisesRegex(ValueError, 'Duplicate payroll'):
            analyze(files, facts, '')

    def test_site_boundary(self):
        self.assertEqual(office_code(4, 'H-420'), ('C-110', None))
        self.assertEqual(office_code(5, 'H-420'), ('H-420', None))
        self.assertIsNotNone(office_code(5, None)[1])

    def test_roof_boundary(self):
        self.assertEqual(roof_code(14), 'R-320')
        self.assertEqual(roof_code(15), 'R-310')

    def test_ride_boundary(self):
        self.assertEqual(dispatcher_code(1), 'C-110')
        self.assertEqual(dispatcher_code(2), 'T-610')

    def test_allowances(self):
        self.assertEqual(allowance('47', 1), (D('0'), D('47')))
        self.assertEqual(allowance('48', 1), (D('1'), D('47')))
        self.assertEqual(allowance('390', 0), (D('390'), D('0')))
        self.assertEqual(allowance('2600', 40), (D('720'), D('1880')))

    def test_catering_boundary_and_missing_time(self):
        self.assertEqual(catering_code(D('39.99'), D('100')), ('F-710', None))
        code, issue = catering_code(D('40'), D('100'))
        self.assertEqual(code, 'F-710')
        self.assertIn('time allocation missing', issue)
        self.assertIsNotNone(catering_code(D(0), D(0))[1])

    def test_certificates(self):
        a, b = '2025-07-07', '2026-07-05'
        self.assertEqual(certificate('A', [], a, b), (D('.60'), None))
        c = {'subcontractor': 'A', 'coverage_from': a, 'coverage_to': '2026-01-31'}
        self.assertEqual(certificate('A', [c], a, b)[0], D('.60'))
        c['coverage_to'] = b
        self.assertEqual(certificate('A', [c], a, b)[0], D(0))
        self.assertIsNotNone(certificate('B', [c], a, b, 'A')[1])

    def test_duplicate_days_and_period(self):
        rows = [{'date': d, 'employee_id': 'X'} for d in ['2025-07-06', '2025-07-07', '2025-07-07', '2026-07-05', '2026-07-06']]
        self.assertEqual(unique_days(period_rows(rows, '2025-07-07', '2026-07-05'), 'X'), 2)

    @patch('sources.download', side_effect=RuntimeError('unavailable'))
    def test_unavailable_never_uses_cache(self, download):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / 'old-output').write_text('preserved')
            with self.assertRaisesRegex(RuntimeError, 'unavailable'):
                collect({'guide_url': 'https://drive.google.com/file/d/abc/view'}, [], t)
            self.assertEqual((Path(t) / 'old-output').read_text(), 'preserved')
            self.assertFalse((Path(t) / 'manifest.json').exists())

    @patch('sources.download', return_value=b'<html>access denied</html>')
    def test_changed_inventory_fails(self, download):
        with self.assertRaisesRegex(ValueError, 'inventory unavailable'):
            inventory('https://drive.google.com/drive/folders/abc')


if __name__ == '__main__':
    unittest.main()
