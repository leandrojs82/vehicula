import csv
import sys
import subprocess
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_preparafrota import APP_DIR, BASE, fixture
sys.path.insert(0, str(APP_DIR))
import preparafrota as app
try:
    import preparafrota_venda as sale
except ImportError:
    sale = None

HEADERS = ['placa_veiculo', 'numero_chassis_veiculo', 'numero_renavam', 'Empresa', 'UF Origem', 'Data Venda', 'UF Venda']
SOLD = ['ABC1D23', '9BWZZZ377VT004251', '00123456789', 'Empresa; "Sul"\nMatriz', 'SP', '09/11/2026 14:30:12', 'RJ']


class SaleFlow(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(sale, 'O fluxo de venda precisa ser implementado')
        self.folder = Path.cwd() / 'work' / ('venda_' + uuid4().hex)
        self.folder.mkdir(parents=True)
        self.source = self.folder / 'Fluxo UF Venda 09-11-2026.xlsx'
        self.reference = self.folder / 'Atualização 09-11-2026.xlsx'
        fixture(self.reference, [BASE])

    def prepare(self, rows, reference=None):
        fixture(self.source, rows, headers=HEADERS)
        return sale.prepare_sales_session(self.source, reference or self.reference)

    def test_join_export_order_semicolon_utf8_dates_and_originals_unchanged(self):
        session = self.prepare([SOLD])
        before = self.source.read_bytes(), self.reference.read_bytes()
        result = app.export_session(session)
        raw = result['csv'].read_bytes()
        self.assertFalse(raw.startswith(b'\xef\xbb\xbf'))
        with result['csv'].open(encoding='utf-8', newline='') as f:
            rows = list(csv.reader(f, delimiter=';'))
        self.assertEqual(rows[0], ['placa_veiculo', 'numero_chassis_veiculo', 'numero_renavam', 'empresa', 'uf_placa', 'veiculo_situacao', 'tipo consulta', 'movimentação', 'data base', 'cnpj', 'uf_venda'])
        self.assertEqual(rows[1], ['ABC1D23', '9BWZZZ377VT004251', '00123456789', 'Empresa; "Sul"\nMatriz', 'SP', 'Ativo', 'Completa', 'Inclusao', '09/11/2026', '10215988000240', 'RJ'])
        self.assertEqual((self.source.read_bytes(), self.reference.read_bytes()), before)
        self.assertIn(self.reference.name, result['report'].read_text(encoding='utf-8'))
        self.assertFalse(any('fora do mapeamento' in i['motivo'] for i in result['issues']))

    def test_lookup_by_plate_preserves_sales_order_and_duplicate_records(self):
        other = BASE.copy()
        other[3], other[6], other[7] = 'DEF4G56', 'Vendido', 'Resumida'
        fixture(self.reference, [BASE, other, BASE])
        first = SOLD.copy()
        first[0] = ' def-4g56 '
        session = self.prepare([first, SOLD, SOLD])
        self.assertEqual(session.pending(), [])
        preview = [v for _, v in session.preview()]
        self.assertEqual([v[0] for v in preview], [' def-4g56 ', 'ABC1D23', 'ABC1D23'])
        self.assertEqual([v[5:7] for v in preview], [['Vendido', 'Resumida'], ['Ativo', 'Completa'], ['Ativo', 'Completa']])

    def test_missing_plate_blocks_output_until_explicit_resolution(self):
        row = SOLD.copy()
        row[0] = 'XYZ9A99'
        session = self.prepare([row])
        self.assertTrue(session.pending())
        with self.assertRaises(ValueError):
            app.export_session(session)
        self.assertFalse(list(self.folder.glob('*.csv')))
        session.resolve_lookup(2, 'Vendido', 'Completa')
        self.assertEqual(session.pending(), [])
        self.assertEqual(session.preview()[0][1][5:7], ['Vendido', 'Completa'])

    def test_conflicting_reference_pairs_require_explicit_choice(self):
        other = BASE.copy()
        other[6], other[7] = 'Vendido', 'Outra'
        fixture(self.reference, [BASE, other])
        session = self.prepare([SOLD])
        self.assertTrue(session.pending())
        self.assertEqual(len(session.lookup_details()[0]['candidatos']), 2)
        with self.assertRaises(ValueError):
            session.correct(2, 'veiculo_situacao', 'Ativo')
        session.resolve_lookup(2, 'Vendido', 'Outra')
        self.assertEqual(session.pending(), [])
        self.assertEqual(session.preview()[0][1][5:7], ['Vendido', 'Outra'])

    def test_changing_plate_recomputes_and_discards_previous_manual_resolution(self):
        session = self.prepare([SOLD])
        session.resolve_lookup(2, 'Manual', 'Manual')
        session.correct(2, 'placa_veiculo', 'XYZ9A99')
        self.assertTrue(session.pending())
        self.assertEqual(session.preview()[0][1][5:7], ['', ''])
        session.correct(2, 'placa_veiculo', 'ABC1D23')
        self.assertEqual(session.pending(), [])
        self.assertEqual(session.preview()[0][1][5:7], ['Ativo', 'Completa'])

    def test_sale_state_is_required_and_constants_cannot_be_overridden(self):
        row = SOLD.copy()
        row[6] = ' '
        session = self.prepare([row])
        self.assertTrue(any(p['coluna'] == 'uf_venda' for p in session.pending()))
        session.correct(2, 'uf_venda', 'MG')
        self.assertEqual(session.pending(), [])
        for name in ('cnpj', 'Movimentação'):
            with self.assertRaises(ValueError):
                session.correct(2, name, 'outro')
        with self.assertRaises(ValueError):
            app.export_session(session, delimiter=',')

    def test_reference_can_be_previous_review_session_or_exported_csv(self):
        reference = app.prepare_session(self.reference)
        reference.correct(2, 'veiculo_situacao', 'Revisado')
        session = self.prepare([SOLD], reference=reference)
        self.assertEqual(session.preview()[0][1][5], 'Revisado')
        saved = app.export_session(reference)['csv']
        session = self.prepare([SOLD], reference=saved)
        self.assertEqual(session.preview()[0][1][5], 'Revisado')

    def test_unknown_columns_do_not_silently_disappear(self):
        fixture(self.source, [SOLD + ['preservar']], headers=HEADERS + ['Extra'])
        with self.assertRaises(ValueError):
            sale.prepare_sales_session(self.source, self.reference)

    def test_incomplete_lookup_and_invalid_sale_date_remain_pending(self):
        reference = BASE.copy()
        reference[7] = ''
        fixture(self.reference, [reference])
        row = SOLD.copy()
        row[5] = '31/02/2026 00:00:00'
        session = self.prepare([row])
        self.assertTrue(any(p['coluna'] == 'DATA BASE' for p in session.pending()))
        session.resolve_lookup(2, 'Ativo', 'Completa')
        self.assertTrue(session.pending())
        session.correct(2, 'DATA BASE', '09/11/2026 10:30')
        self.assertEqual(session.pending(), [])

    def test_typed_excel_sale_date_and_numeric_zero_mask(self):
        fixture(self.source, [SOLD], headers=HEADERS, typed_date=True, typed_date_column=6, numeric=True)
        session = sale.prepare_sales_session(self.source, self.reference)
        self.assertEqual(session.preview()[0][1][8], '09/11/2026')
        self.assertEqual(session.preview()[0][1][2], '00123456789')

    def test_sales_cli_is_integrated_and_uses_required_format(self):
        fixture(self.source, [SOLD], headers=HEADERS)
        run = subprocess.run([sys.executable, str(APP_DIR / 'preparafrota.py'), str(self.source), '--fluxo', 'venda', '--referencia', str(self.reference)], capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        with self.source.with_suffix('.csv').open(encoding='utf-8', newline='') as f:
            data = list(csv.reader(f, delimiter=';'))
        self.assertEqual(len(data[1]), 11)
        self.assertEqual(data[1][-1], 'RJ')

    def test_error_in_reference_does_not_become_an_automatic_lookup_value(self):
        fixture(self.reference, [BASE], error_column=7)
        session = self.prepare([SOLD])
        self.assertTrue(session.pending())
        self.assertTrue(session.reference_warnings)
        session.resolve_lookup(2, 'Ativo', 'Completa')
        result = app.export_session(session)
        self.assertIn('#N/A', result['report'].read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
