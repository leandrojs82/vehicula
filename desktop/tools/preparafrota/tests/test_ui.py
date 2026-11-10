import sys
import tkinter as tk
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_processing import UPDATE, UPDATE_HEADERS, SALE, SALE_HEADERS, APP_DIR
from fixtures import fixture
sys.path.insert(0, str(APP_DIR))
try:
    from preparafrota.ui import App
except ImportError:
    App = None


class MinimalUI(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(App, 'A nova interface precisa ser criada')
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.ui = App(self.root)
        self.folder = Path.cwd() / 'work' / ('v5ui_' + uuid4().hex)
        self.folder.mkdir(parents=True)
        self.update, self.sale = self.folder / 'update.xlsx', self.folder / 'sale.xlsx'
        fixture(self.update, [UPDATE], headers=UPDATE_HEADERS)
        fixture(self.sale, [SALE], headers=SALE_HEADERS)

    def test_auto_detect_sale_and_resume_after_reference_without_reselecting(self):
        self.ui.load_file(self.sale)
        self.assertEqual(self.ui.session.flow, 'venda')
        self.assertTrue(self.ui.export_button.instate(['disabled']))
        self.ui.load_reference(self.update)
        self.assertEqual(self.ui.session.source, self.sale.resolve())
        self.assertTrue(self.ui.export_button.instate(['!disabled']))
        self.assertEqual(self.ui.session.rows[0].values['uf_venda'], 'RJ')

    def test_single_table_blank_editor_unlocks_export(self):
        row = UPDATE.copy()
        row[5] = ' '
        fixture(self.update, [row], headers=UPDATE_HEADERS)
        self.ui.load_file(self.update)
        self.assertTrue(self.ui.export_button.instate(['disabled']))
        self.assertEqual(self.ui.view_var.get(), 'Pendências')
        item = self.ui.tree.get_children()[0]
        self.ui.tree.selection_set(item)
        self.ui.select_item()
        self.ui.value_var.set('RJ')
        self.ui.apply_edit()
        self.assertTrue(self.ui.export_button.instate(['!disabled']))
        self.assertEqual(self.ui.session.rows[0].values['uf_placa'], 'RJ')

    def test_failed_load_keeps_previous_session(self):
        self.ui.load_file(self.update)
        previous = self.ui.session
        with self.assertRaises(ValueError):
            self.ui.load_file(self.folder / 'missing.xlsx')
        self.assertIs(self.ui.session, previous)

    def test_conflicting_lookup_can_be_confirmed_in_same_table(self):
        other = UPDATE.copy()
        other[6:8] = ['Vendido', 'Outra']
        fixture(self.update, [UPDATE, other], headers=UPDATE_HEADERS)
        self.ui.load_file(self.sale)
        self.ui.load_reference(self.update)
        self.ui.view_var.set('Cruzamento')
        self.ui.refresh()
        self.ui.tree.selection_set(self.ui.tree.get_children()[0])
        self.ui.select_item()
        self.ui.situation_var.set('Vendido')
        self.ui.query_var.set('Outra')
        self.ui.confirm_lookup()
        self.assertTrue(self.ui.export_button.instate(['!disabled']))
        self.assertEqual(self.ui.session.rows[0].values['tipo consulta'], 'Outra')

    def test_movement_view_limits_fifty_without_limiting_export_data(self):
        fixture(self.update, [UPDATE] * 65, headers=UPDATE_HEADERS)
        self.ui.load_file(self.update)
        self.ui.view_var.set('Movimentação')
        self.ui.refresh()
        self.assertEqual(len(self.ui.tree.get_children()), 50)
        self.assertEqual(len(self.ui.session.rows), 65)

    def test_new_week_update_replaces_previous_explicit_reference(self):
        self.ui.load_file(self.sale)
        self.ui.load_reference(self.update)
        new_reference = self.folder / 'semana_nova.xlsx'
        row = UPDATE.copy()
        row[6] = 'Atualizado na nova semana'
        fixture(new_reference, [row], headers=UPDATE_HEADERS)
        self.ui.load_file(new_reference)
        self.ui.load_file(self.sale)
        self.assertEqual(self.ui.session.rows[0].values['veiculo_situacao'], 'Atualizado na nova semana')

    def test_readonly_preview_selection_clears_previous_cell_editor(self):
        self.ui.load_file(self.update)
        self.ui.view_var.set('Prévia CSV')
        self.ui.refresh()
        self.ui._show_editor(('cell', 2, 'placa_veiculo'))
        self.assertIsNotNone(self.ui.selected)
        self.ui.tree.selection_set(self.ui.tree.get_children()[0])
        self.ui.select_item()
        self.assertIsNone(self.ui.selected)
        self.assertEqual(self.ui.editor.winfo_manager(), '')

    def test_pending_confirmation_button_accepts_saved_value_and_unlocks_export(self):
        row = UPDATE.copy()
        row[5] = ''
        fixture(self.update, [row], headers=UPDATE_HEADERS)
        self.ui.load_file(self.update)
        self.ui.tree.selection_set(self.ui.tree.get_children()[0])
        self.ui.select_item()
        self.assertTrue(self.ui.confirm_button.instate(['!disabled']))
        self.ui.confirm_current()
        self.assertEqual(self.ui.session.rows[0].values['uf_placa'], '')
        self.assertTrue(self.ui.export_button.instate(['!disabled']))

    def test_extra_query_button_only_appears_for_missing_matches_and_fills_them(self):
        self.ui.load_file(self.sale)
        self.assertEqual(self.ui.supplement_button.winfo_manager(), '')
        row = SALE.copy()
        row[0] = 'DEF4G56'
        fixture(self.sale, [row], headers=SALE_HEADERS)
        self.ui.load_file(self.sale)
        self.ui.load_reference(self.update)
        self.assertEqual(self.ui.supplement_button.winfo_manager(), 'pack')
        extra = self.folder / 'complemento.xlsx'
        reference = UPDATE.copy()
        reference[3] = 'DEF4G56'
        fixture(extra, [reference], headers=UPDATE_HEADERS)
        self.ui.load_complement(extra)
        self.assertEqual(self.ui.supplement_button.winfo_manager(), '')
        self.assertTrue(self.ui.export_button.instate(['!disabled']))

    def test_warnings_view_contains_only_invalid_plate_formats(self):
        row = UPDATE.copy()
        row[3] = 'ABC12D3'
        fixture(self.update, [UPDATE, row], headers=UPDATE_HEADERS, error_column=7)
        self.ui.load_file(self.update)
        self.ui.view_var.set('Avisos')
        self.ui.refresh()
        rows = self.ui.tree.get_children()
        self.assertEqual(len(rows), 1)
        self.assertIn('ABC12D3', self.ui.tree.item(rows[0], 'values'))


if __name__ == '__main__':
    unittest.main()
