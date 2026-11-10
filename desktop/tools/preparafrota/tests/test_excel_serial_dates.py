import sys
import unittest
from datetime import datetime
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_processing import APP_DIR, UPDATE, UPDATE_HEADERS, SALE, SALE_HEADERS
from fixtures import fixture
sys.path.insert(0, str(APP_DIR))
from preparafrota.dates import normalize_date
from preparafrota import processor, validation


class ExcelSerialDates(unittest.TestCase):
    def setUp(self):
        self.folder = Path.cwd() / 'work' / ('serial_dates_' + uuid4().hex)
        self.folder.mkdir(parents=True)
        self.update, self.sale = self.folder / 'update.xlsx', self.folder / 'sale.xlsx'
        fixture(self.update, [UPDATE], headers=UPDATE_HEADERS)

    def test_numbers_shown_in_screenshot_convert_to_calendar_date(self):
        for value in (46134.70949074074, '46134.70949074074', '46134,70949074074', 46134, '46134'):
            with self.subTest(value=value):
                self.assertEqual(normalize_date(value), '22/04/2026')

    def test_native_serial_without_date_style_converts_only_date_field(self):
        row = SALE.copy()
        row[2] = '46134.70949074074'
        fixture(self.sale, [row], headers=SALE_HEADERS, numeric_cells={(2, 6): '46134.70949074074'})
        session = processor.load_session(self.sale, reference=self.update)
        self.assertEqual(session.rows[0].values['data base'], '22/04/2026')
        self.assertEqual(session.rows[0].values['numero_renavam'], '46134.70949074074')
        self.assertEqual(validation.pending(session), [])

    def test_workbook_date_system_is_respected_for_unformatted_serial(self):
        fixture(self.sale, [SALE], headers=SALE_HEADERS, epoch_1904=True, numeric_cells={(2, 6): '44672.70949074074'})
        session = processor.load_session(self.sale, reference=self.update)
        self.assertEqual(session.rows[0].values['data base'], '22/04/2026')

    def test_invalid_serials_are_reported_without_overwriting_original(self):
        values = ['NaN', 'inf', '-1', '0', '60', '999999999999', 'sem data']
        rows = []
        for value in values:
            row = SALE.copy()
            row[5] = value
            rows.append(row)
        fixture(self.sale, rows, headers=SALE_HEADERS)
        session = processor.load_session(self.sale, reference=self.update)
        self.assertEqual([row.values['data base'] for row in session.rows], values)
        self.assertEqual(len(validation.pending(session)), len(values))
        self.assertTrue(all('convert' in issue.reason.lower() or 'data inválida' in issue.reason.lower() for issue in validation.pending(session)))

    def test_manual_numeric_date_edit_uses_same_workbook_calendar(self):
        row = SALE.copy()
        row[5] = 'sem data'
        fixture(self.sale, [row], headers=SALE_HEADERS, epoch_1904=True)
        session = processor.load_session(self.sale, reference=self.update)
        processor.edit_cell(session, 2, 'data base', '44672.70949074074')
        self.assertEqual(session.rows[0].values['data base'], '22/04/2026')
        self.assertEqual(validation.pending(session), [])

    def test_fractional_hour_is_removed_without_rounding_into_next_day(self):
        self.assertEqual(normalize_date('46134.99999999999'), '22/04/2026')


if __name__ == '__main__':
    unittest.main()
