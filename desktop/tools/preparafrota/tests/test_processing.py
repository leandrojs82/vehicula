import csv
import importlib.util
import subprocess
import sys
import unittest
from datetime import datetime
from pathlib import Path
from uuid import uuid4

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixtures import fixture

if importlib.util.find_spec('preparafrota'):
    from preparafrota import processor, validation, exporter
else:
    processor = validation = exporter = None

UPDATE_HEADERS = ['Empresa', 'Produto', 'numero_renavam', 'placa_veiculo', 'numero_chassis_veiculo', 'UF_Placa', 'veiculo_situacao', 'Tipo consulta', 'Movimentação', 'DATA BASE']
UPDATE = [' Empresa; "Sul"\nMatriz ', 'Plano', '00123456789', 'ABC1D23', '9BWZZZ377VT004251', 'SP', 'Ativo', 'Completa', 'Incluir Consulta', '09/11/2026']
SALE_HEADERS = ['placa_veiculo', 'numero_chassis_veiculo', 'numero_renavam', 'Empresa', 'UF Origem', 'Data Venda', 'UF Venda']
SALE = ['ABC1D23', '9BWZZZ377VT004251', '00123456789', 'Empresa; "Sul"\nMatriz', 'SP', '09/11/2026 14:30:12', 'RJ']
OUTPUT = ['placa_veiculo', 'numero_chassis_veiculo', 'numero_renavam', 'empresa', 'uf_placa', 'veiculo_situacao', 'tipo consulta', 'movimentação', 'data base', 'cnpj', 'uf_venda']


class Processing(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(processor, 'A nova implementação precisa ser criada')
        self.folder = Path.cwd() / 'work' / ('v5_' + uuid4().hex)
        self.folder.mkdir(parents=True)
        self.update = self.folder / 'atualizacao.xlsx'
        self.sale = self.folder / 'venda.xlsx'
        fixture(self.update, [UPDATE], headers=UPDATE_HEADERS)
        fixture(self.sale, [SALE], headers=SALE_HEADERS)

    def read_output(self, session):
        output = exporter.export_csv(session)
        self.assertTrue(output.csv.read_bytes().startswith(b'\xef\xbb\xbf'))
        with output.csv.open(encoding='utf-8-sig', newline='') as f:
            return output, list(csv.reader(f, delimiter=';'))

    def test_update_exact_mapping_order_preservation_and_product_removed(self):
        rows = []
        for movement in ['Incluir Consulta', 'Manter Consulta', 'Desativar']:
            row = UPDATE.copy()
            row[8] = movement
            row[1] = ''  # Produto é removido, sem exigir correção inútil.
            rows.append(row)
        fixture(self.update, rows, headers=UPDATE_HEADERS)
        before = self.update.read_bytes()
        session = processor.load_session(self.update)
        result, out = self.read_output(session)
        self.assertEqual(out[0], OUTPUT)
        self.assertEqual([r[7] for r in out[1:]], ['Inclusao', 'Inclusao', 'Exclusao'])
        self.assertEqual(out[1], ['ABC1D23', '9BWZZZ377VT004251', '00123456789', ' Empresa; "Sul"\nMatriz ', 'SP', 'Ativo', 'Completa', 'Inclusao', '09/11/2026', '10215988000240', ''])
        self.assertEqual(self.update.read_bytes(), before)
        self.assertNotIn('produto', session.rows[0].values)
        self.assertTrue(result.report.exists())

    def test_sale_lookup_from_update_and_date_only(self):
        before = self.sale.read_bytes(), self.update.read_bytes()
        session = processor.load_session(self.sale, reference=self.update)
        _, out = self.read_output(session)
        self.assertEqual(out[0], OUTPUT)
        self.assertEqual(out[1][4:], ['SP', 'Ativo', 'Completa', 'Inclusao', '09/11/2026', '10215988000240', 'RJ'])
        self.assertEqual((self.sale.read_bytes(), self.update.read_bytes()), before)

    def test_reference_required_then_can_be_added_without_reselecting_sale(self):
        session = processor.load_session(self.sale)
        self.assertEqual(session.flow, 'venda')
        self.assertTrue(validation.pending(session))
        with self.assertRaises(ValueError):
            exporter.export_csv(session)
        processor.set_reference(session, self.update)
        self.assertEqual(validation.pending(session), [])

    def test_missing_plate_is_explicitly_resolved_and_plate_change_recomputes(self):
        row = SALE.copy()
        row[0] = 'XYZ9A99'
        fixture(self.sale, [row], headers=SALE_HEADERS)
        session = processor.load_session(self.sale, reference=self.update)
        self.assertTrue(validation.pending(session))
        processor.resolve_lookup(session, 2, 'Vendido', 'Simples')
        self.assertEqual(validation.pending(session), [])
        processor.edit_cell(session, 2, 'placa_veiculo', 'ABC1D23')
        self.assertEqual(session.rows[0].values['veiculo_situacao'], 'Ativo')

    def test_identical_reference_duplicates_do_not_expand_sales(self):
        fixture(self.update, [UPDATE, UPDATE], headers=UPDATE_HEADERS)
        row = SALE.copy()
        row[0] = ' abc-1d23 '
        fixture(self.sale, [row, row], headers=SALE_HEADERS)
        session = processor.load_session(self.sale, reference=self.update)
        _, out = self.read_output(session)
        self.assertEqual(len(out), 3)
        self.assertEqual(out[1][0], ' abc-1d23 ')

    def test_conflicting_pairs_block_and_allow_explicit_pair_choice(self):
        other = UPDATE.copy()
        other[6:8] = ['Vendido', 'Outra']
        fixture(self.update, [UPDATE, other], headers=UPDATE_HEADERS)
        session = processor.load_session(self.sale, reference=self.update)
        self.assertTrue(validation.pending(session))
        with self.assertRaises(ValueError):
            exporter.export_csv(session)
        processor.resolve_lookup(session, 2, 'Vendido', 'Outra')
        self.assertEqual(validation.pending(session), [])
        self.assertEqual(session.rows[0].values['tipo consulta'], 'Outra')

    def test_whitespace_blank_blocks_and_bulk_fill_keeps_other_values(self):
        row = UPDATE.copy()
        row[5] = '  '
        fixture(self.update, [row, row, UPDATE], headers=UPDATE_HEADERS)
        session = processor.load_session(self.update)
        with self.assertRaises(ValueError):
            exporter.export_csv(session)
        self.assertFalse(list(self.folder.glob('*.csv')))
        processor.edit_cell(session, 2, 'uf_placa', 'RJ', all_empty=True)
        self.assertEqual([r.values['uf_placa'] for r in session.rows], ['RJ', 'RJ', 'SP'])
        self.assertEqual(validation.pending(session), [])

    def test_internal_empty_row_is_kept_and_blocks_export(self):
        fixture(self.update, [UPDATE, [None] * len(UPDATE), UPDATE], headers=UPDATE_HEADERS)
        session = processor.load_session(self.update)
        self.assertEqual(len(session.rows), 3)
        self.assertTrue(any(i.row == 3 for i in validation.pending(session)))

    def test_date_fallback_and_impossible_date_not_silently_emptied(self):
        for value, expected in [('2026-11-09T14:30:12', '09/11/2026'), ('9/11/2026 14:30', '09/11/2026'), ('31/02/2026', None), ('11/09/26', None)]:
            with self.subTest(value=value):
                row = SALE.copy()
                row[5] = value
                fixture(self.sale, [row], headers=SALE_HEADERS)
                session = processor.load_session(self.sale, reference=self.update)
                if expected:
                    self.assertEqual(session.rows[0].values['data base'], expected)
                else:
                    self.assertEqual(session.rows[0].values['data base'], value)
                    self.assertTrue(validation.pending(session))

    def test_native_excel_date_and_zero_mask_are_preserved(self):
        fixture(self.sale, [SALE], headers=SALE_HEADERS, typed_date=True, typed_date_column=6, numeric=True)
        session = processor.load_session(self.sale, reference=self.update)
        self.assertEqual(session.rows[0].values['data base'], '09/11/2026')
        self.assertEqual(session.rows[0].values['numero_renavam'], '00123456789')

    def test_schema_errors_are_clear_and_extra_columns_never_disappear(self):
        for headers in [SALE_HEADERS[:-1], SALE_HEADERS + ['Extra'], SALE_HEADERS + ['Empresa']]:
            with self.subTest(headers=headers):
                fixture(self.sale, [SALE], headers=headers)
                with self.assertRaises(ValueError):
                    processor.load_session(self.sale)
        with self.assertRaisesRegex(ValueError, 'encontrado'):
            processor.load_session(self.folder / 'ausente.xlsx')

    def test_unknown_movement_is_pending_until_chosen(self):
        row = UPDATE.copy()
        row[8] = 'Revisar'
        fixture(self.update, [row], headers=UPDATE_HEADERS)
        session = processor.load_session(self.update)
        self.assertTrue(validation.pending(session))
        processor.edit_cell(session, 2, 'movimentação', 'Exclusao')
        self.assertEqual(validation.pending(session), [])

    def test_sale_uf_venda_required_and_fixed_columns_protected(self):
        row = SALE.copy()
        row[-1] = ''
        fixture(self.sale, [row], headers=SALE_HEADERS)
        session = processor.load_session(self.sale, reference=self.update)
        self.assertTrue(any(i.column == 'uf_venda' for i in validation.pending(session)))
        for column in ('cnpj', 'movimentação'):
            with self.assertRaises(ValueError):
                processor.edit_cell(session, 2, column, 'Outro')
        processor.edit_cell(session, 2, 'uf_venda', 'MG')
        self.assertEqual(validation.pending(session), [])

    def test_error_in_reference_requires_correction_and_report_keeps_provenance(self):
        fixture(self.update, [UPDATE], headers=UPDATE_HEADERS, error_column=7)
        session = processor.load_session(self.sale, reference=self.update)
        self.assertTrue(validation.pending(session))
        processor.resolve_lookup(session, 2, 'Ativo', 'Completa')
        result, _ = self.read_output(session)
        report = result.report.read_text(encoding='utf-8')
        self.assertIn('#N/A', report)
        self.assertIn(self.update.name, report)

    def test_reference_can_be_revised_session_or_generated_csv(self):
        reference = processor.load_session(self.update)
        processor.edit_cell(reference, 2, 'veiculo_situacao', 'Revisado')
        result, _ = self.read_output(reference)
        for source in (reference, result.csv):
            session = processor.load_session(self.sale, reference=source)
            self.assertEqual(session.rows[0].values['veiculo_situacao'], 'Revisado')

    def test_movements_preview_is_original_to_final_first_fifty_only(self):
        fixture(self.update, [UPDATE] * 60, headers=UPDATE_HEADERS)
        session = processor.load_session(self.update)
        changes = processor.movement_preview(session)
        self.assertEqual(len(changes), 50)
        self.assertEqual(changes[0]['antes'], 'Incluir Consulta')
        self.assertEqual(changes[0]['depois'], 'Inclusao')
        self.assertEqual(changes[-1]['linha'], 51)
        self.assertEqual(len(session.rows), 60)

    def test_existing_output_is_not_overwritten(self):
        session = processor.load_session(self.update)
        first, _ = self.read_output(session)
        before = first.csv.read_bytes()
        second, _ = self.read_output(session)
        self.assertNotEqual(first.csv, second.csv)
        self.assertEqual(first.csv.read_bytes(), before)

    def test_console_auto_detect_and_clear_errors(self):
        run = subprocess.run([sys.executable, str(APP_DIR / 'main.py'), str(self.sale), '--referencia', str(self.update)], capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(self.sale.with_suffix('.csv').exists())
        run = subprocess.run([sys.executable, str(APP_DIR / 'main.py'), str(self.folder / 'ausente.xlsx')], capture_output=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn(b'Erro', run.stderr)

    def test_invalid_xml_has_clear_reading_error(self):
        import zipfile
        with zipfile.ZipFile(self.update) as archive:
            parts = {name: archive.read(name) for name in archive.namelist()}
        parts['xl/worksheets/sheet1.xml'] = b'<worksheet><broken'
        with zipfile.ZipFile(self.update, 'w') as archive:
            for name, content in parts.items():
                archive.writestr(name, content)
        with self.assertRaisesRegex(ValueError, 'ler o Excel'):
            processor.load_session(self.update)

    def test_formula_without_saved_result_stays_pending_until_corrected(self):
        fixture(self.update, [UPDATE], headers=UPDATE_HEADERS, formula=True)
        session = processor.load_session(self.update)
        self.assertTrue(any(i.column == 'empresa' for i in validation.pending(session)))
        processor.edit_cell(session, 2, 'empresa', 'Empresa corrigida')
        self.assertEqual(validation.pending(session), [])

    def test_multiple_sheets_require_explicit_choice(self):
        fixture(self.update, [UPDATE], headers=UPDATE_HEADERS, extra_sheet=True)
        with self.assertRaisesRegex(ValueError, 'aba'):
            processor.load_session(self.update)
        session = processor.load_session(self.update, sheet='Dados')
        self.assertEqual(len(session.rows), 1)


if __name__ == '__main__':
    unittest.main()
