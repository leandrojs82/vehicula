import csv
import sys
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_processing import APP_DIR, UPDATE, UPDATE_HEADERS, SALE, SALE_HEADERS
from fixtures import fixture
sys.path.insert(0, str(APP_DIR))
from preparafrota import processor, validation, exporter


class ReviewActions(unittest.TestCase):
    def setUp(self):
        self.folder = Path.cwd() / 'work' / ('review_' + uuid4().hex)
        self.folder.mkdir(parents=True)
        self.update, self.sale, self.extra = [self.folder / name for name in ('update.xlsx', 'sale.xlsx', 'extra.xlsx')]
        fixture(self.update, [UPDATE], headers=UPDATE_HEADERS)
        fixture(self.sale, [SALE], headers=SALE_HEADERS)

    def test_confirm_current_value_is_scoped_and_audited_without_changing_data(self):
        row = UPDATE.copy()
        row[5], row[9] = '', 'sem data'
        fixture(self.update, [row], headers=UPDATE_HEADERS)
        session = processor.load_session(self.update)
        processor.confirm_pending(session, 2, 'uf_placa')
        self.assertEqual([i.column for i in validation.pending(session)], ['data base'])
        processor.confirm_pending(session, 2, 'data base')
        self.assertEqual(validation.pending(session), [])
        result = exporter.export_csv(session)
        with result.csv.open(encoding='utf-8-sig', newline='') as stream:
            data = list(csv.reader(stream, delimiter=';'))
        self.assertEqual(data[1][4], '')
        self.assertEqual(data[1][8], 'sem data')
        self.assertIn('Confirmado como está', result.report.read_text(encoding='utf-8'))

    def test_editing_a_confirmed_field_invalidates_its_confirmation(self):
        row = UPDATE.copy()
        row[5] = ''
        fixture(self.update, [row], headers=UPDATE_HEADERS)
        session = processor.load_session(self.update)
        processor.confirm_pending(session, 2, 'uf_placa')
        processor.edit_cell(session, 2, 'uf_placa', 'RJ')
        self.assertFalse(session.confirmations)

    def test_lookup_or_missing_reference_cannot_be_accepted_without_lookup_values(self):
        session = processor.load_session(self.sale)
        with self.assertRaises(ValueError):
            processor.confirm_pending(session, 0, 'referência')
        row = SALE.copy()
        row[0] = 'XYZ9A99'
        fixture(self.sale, [row], headers=SALE_HEADERS)
        session = processor.load_session(self.sale, reference=self.update)
        with self.assertRaises(ValueError):
            processor.confirm_pending(session, 2, 'cruzamento')

    def test_only_plates_outside_old_and_mercosul_formats_create_warnings(self):
        good = ['ABC1234', 'ABC-1234', 'ABC1D23', 'ABC-1D23', 'abc1234', ' abc1d23 ']
        bad = ['ABC12D3', 'AB12345', 'ABC12345', 'ABC1_23', 'АBC1234', 'ABC 1234']
        rows = []
        for plate in good + bad:
            row = UPDATE.copy()
            row[3] = plate
            row[0] = '  Empresa rara  '
            rows.append(row)
        fixture(self.update, rows, headers=UPDATE_HEADERS)
        session = processor.load_session(self.update)
        warnings = validation.warnings(session)
        self.assertEqual([i.value for i in warnings], bad)
        self.assertTrue(all(i.column == 'placa_veiculo' for i in warnings))

    def test_complement_fills_only_missing_matches_preserves_resolved_and_records_origin(self):
        rows = [SALE.copy() for _ in range(3)]
        rows[1][0], rows[2][0] = 'XYZ9A99', 'DEF4G56'
        fixture(self.sale, rows, headers=SALE_HEADERS)
        session = processor.load_session(self.sale, reference=self.update)
        processor.resolve_lookup(session, 3, 'Manual', 'Manual')
        extra_rows = []
        for plate in ('ABC1D23', 'XYZ9A99', 'DEF4G56'):
            row = UPDATE.copy()
            row[3], row[6], row[7] = plate, 'Complementar', 'Consulta extra'
            extra_rows.append(row)
        fixture(self.extra, extra_rows, headers=UPDATE_HEADERS)
        count = processor.add_supplemental_reference(session, self.extra)
        self.assertEqual(count, 1)
        self.assertEqual([r.values['veiculo_situacao'] for r in session.rows], ['Ativo', 'Manual', 'Complementar'])
        self.assertEqual(len(session.rows), 3)
        self.assertEqual(validation.pending(session), [])
        result = exporter.export_csv(session)
        self.assertIn(self.extra.name, result.report.read_text(encoding='utf-8'))

    def test_complement_is_available_only_for_unmatched_plates(self):
        session = processor.load_session(self.sale, reference=self.update)
        self.assertEqual(processor.missing_lookup_rows(session), [])
        with self.assertRaises(ValueError):
            processor.add_supplemental_reference(session, self.extra)

    def test_conflicting_complement_does_not_pick_a_pair_or_replace_existing_lookup(self):
        row = SALE.copy()
        row[0] = 'DEF4G56'
        fixture(self.sale, [row], headers=SALE_HEADERS)
        candidates = [UPDATE.copy(), UPDATE.copy()]
        candidates[0][3] = candidates[1][3] = 'DEF4G56'
        candidates[1][6] = 'Outra situação'
        fixture(self.extra, candidates, headers=UPDATE_HEADERS)
        session = processor.load_session(self.sale, reference=self.update)
        self.assertEqual(processor.add_supplemental_reference(session, self.extra), 0)
        self.assertTrue(validation.pending(session))
        self.assertEqual(session.rows[0].values['veiculo_situacao'], '')
        self.assertEqual(len(session.matches[2].candidates), 2)
        self.assertEqual(processor.missing_lookup_rows(session), [])

    def test_changing_plate_can_reuse_complement_but_changing_main_reference_resets_it(self):
        row = UPDATE.copy()
        row[3] = 'DEF4G56'
        fixture(self.extra, [row], headers=UPDATE_HEADERS)
        sold = SALE.copy()
        sold[0] = 'DEF4G56'
        fixture(self.sale, [sold], headers=SALE_HEADERS)
        session = processor.load_session(self.sale, reference=self.update)
        processor.add_supplemental_reference(session, self.extra)
        processor.edit_cell(session, 2, 'placa_veiculo', 'ABC1D23')
        processor.edit_cell(session, 2, 'placa_veiculo', 'DEF4G56')
        self.assertEqual(validation.pending(session), [])
        processor.set_reference(session, self.update)
        self.assertTrue(validation.pending(session))
        self.assertEqual(session.supplemental_references, [])

    def test_confirmed_blank_sale_plate_still_requires_explicit_lookup_pair(self):
        row = SALE.copy()
        row[0] = ''
        fixture(self.sale, [row], headers=SALE_HEADERS)
        session = processor.load_session(self.sale, reference=self.update)
        with self.assertRaises(ValueError):
            processor.resolve_lookup(session, 2, 'Ativo', 'Completa')
        processor.confirm_pending(session, 2, 'placa_veiculo')
        self.assertTrue(any(item.column == 'cruzamento' for item in validation.pending(session)))
        processor.resolve_lookup(session, 2, 'Ativo', 'Completa')
        self.assertEqual(validation.pending(session), [])
        result = exporter.export_csv(session)
        with result.csv.open(encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.reader(stream, delimiter=';'))
        self.assertEqual(rows[1][0], '')
        self.assertEqual(rows[1][5:7], ['Ativo', 'Completa'])


if __name__ == '__main__':
    unittest.main()
