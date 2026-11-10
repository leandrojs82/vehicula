import sys
import tkinter as tk
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_preparafrota import APP_DIR, BASE, fixture
sys.path.insert(0, str(APP_DIR))
try:
    from preparafrota_visual import PreparaFrotaWindow
except ImportError:
    PreparaFrotaWindow = None


class VisualReview(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(PreparaFrotaWindow, 'A interface visual ainda precisa ser implementada')
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.ui = PreparaFrotaWindow(self.root)

    def test_export_is_disabled_until_every_blank_is_corrected(self):
        from uuid import uuid4
        folder = Path.cwd() / 'work' / ('visual_' + uuid4().hex)
        folder.mkdir(parents=True)
        source = folder / 'entrada.xlsx'
        row = BASE.copy()
        row[5] = ' '
        fixture(source, [row])
        self.assertTrue(self.ui.export_button.instate(['disabled']))
        self.ui.load_path(source, 'Dados')
        self.assertTrue(self.ui.export_button.instate(['disabled']))
        pending = self.ui.pending_tree.get_children()
        self.assertEqual(len(pending), 1)
        self.ui.pending_tree.selection_set(pending[0])
        self.ui.select_pending()
        self.ui.value_var.set('RJ')
        self.ui.apply_correction()
        self.assertEqual(self.ui.session.pending(), [])
        self.assertTrue(self.ui.export_button.instate(['!disabled']))
        item = self.ui.preview_tree.get_children()[0]
        self.assertEqual(self.ui.preview_tree.item(item, 'values')[5], 'RJ')
        self.assertFalse(source.with_suffix('.csv').exists())

    def test_alert_after_preview_limit_can_be_corrected(self):
        from uuid import uuid4
        folder = Path.cwd() / 'work' / ('visual_' + uuid4().hex)
        folder.mkdir(parents=True)
        source = folder / 'muitos.xlsx'
        rows = [BASE.copy() for _ in range(501)]
        rows[-1][8] = 'Revisar'
        fixture(source, rows)
        self.ui.load_path(source, 'Dados')
        self.assertEqual(len(self.ui.preview_tree.get_children()), 500)
        index = next(i for i, a in enumerate(self.ui.alert_items) if a['linha'] == 502 and a['coluna'] == 'Movimentação')
        self.ui.alerts_tree.selection_set(str(index))
        self.ui.select_alert()
        self.ui.alert_value_var.set('Incluir Consulta')
        self.ui.apply_alert_correction()
        self.assertEqual(self.ui.session.rows[-1][1]['Movimentação'], 'Incluir Consulta')

    def test_movement_preview_before_and_after_and_new_app_name(self):
        from uuid import uuid4
        folder = Path.cwd() / 'work' / ('visual_' + uuid4().hex)
        folder.mkdir(parents=True)
        source = folder / 'movimentos.xlsx'
        rows = [BASE.copy() for _ in range(53)]
        rows[1][8] = 'Desativar'
        fixture(source, rows)
        self.ui.load_path(source, 'Dados')
        self.assertEqual(self.root.title(), 'PreparaFrota | Preparação de placas')
        items = self.ui.movements_tree.get_children()
        self.assertEqual(len(items), 50)
        self.assertEqual(self.ui.movements_tree.item(items[1], 'values'), ('3', 'ABC1D23', 'Desativar', 'Exclusao'))
        self.assertIn('50 de 53', self.ui.movements_var.get())
        self.assertEqual(self.ui.notebook.select(), str(self.ui.movements_tab))

    def test_sales_flow_reference_lookup_review_and_fixed_separator(self):
        from uuid import uuid4
        from test_venda import SOLD, HEADERS
        folder = Path.cwd() / 'work' / ('visual_' + uuid4().hex)
        folder.mkdir(parents=True)
        source, reference = folder / 'venda.xlsx', folder / 'referencia.xlsx'
        fixture(reference, [BASE])
        row = SOLD.copy()
        row[0] = 'XYZ9A99'
        fixture(source, [row], headers=HEADERS)
        self.ui.flow_var.set('Fluxo UF Venda')
        self.ui.change_flow()
        self.ui.set_reference(reference)
        self.ui.load_path(source, 'Dados')
        self.assertTrue(self.ui.export_button.instate(['disabled']))
        self.assertEqual(self.ui.separator_var.get(), 'Ponto e vírgula (;)')
        self.assertTrue(self.ui.separator_combo.instate(['disabled']))
        self.ui.lookup_tree.selection_set('2')
        self.ui.select_lookup()
        self.ui.situation_var.set('Vendido')
        self.ui.query_var.set('Completa')
        self.ui.confirm_lookup()
        self.assertEqual(self.ui.session.pending(), [])
        self.assertTrue(self.ui.export_button.instate(['!disabled']))
        self.assertEqual(self.ui.session.preview()[0][1][-1], 'RJ')

    def test_switching_flow_removes_loaded_export_and_retains_reviewed_reference(self):
        from uuid import uuid4
        folder = Path.cwd() / 'work' / ('visual_' + uuid4().hex)
        folder.mkdir(parents=True)
        source = folder / 'atualizacao.xlsx'
        fixture(source, [BASE])
        self.ui.load_path(source, 'Dados')
        self.ui.flow_var.set('Fluxo UF Venda')
        self.ui.change_flow()
        self.assertIsNone(self.ui.session)
        self.assertTrue(self.ui.export_button.instate(['disabled']))
        self.assertIsNotNone(self.ui.reference)

    def test_sales_file_opened_in_default_update_mode_is_recognized(self):
        from uuid import uuid4
        from test_venda import SOLD, HEADERS
        folder = Path.cwd() / 'work' / ('recognition_' + uuid4().hex)
        folder.mkdir(parents=True)
        source, reference = folder / 'nome_qualquer.xlsx', folder / 'referencia.xlsx'
        fixture(reference, [BASE])
        fixture(source, [SOLD], headers=HEADERS)
        self.ui.set_reference(reference)
        self.ui.load_path(source, 'Dados')
        self.assertEqual(self.ui.flow_var.get(), 'Fluxo UF Venda')
        self.assertEqual(self.ui.session.preview()[0][1][-1], 'RJ')
        self.assertTrue(self.ui.export_button.instate(['!disabled']))

    def test_missing_reference_keeps_sale_selection_and_resumes_after_reference(self):
        from uuid import uuid4
        from test_venda import SOLD, HEADERS
        folder = Path.cwd() / 'work' / ('recognition_' + uuid4().hex)
        folder.mkdir(parents=True)
        source, reference = folder / 'venda.xlsx', folder / 'referencia.xlsx'
        fixture(reference, [BASE])
        fixture(source, [SOLD], headers=HEADERS)
        with self.assertRaisesRegex(ValueError, 'referência'):
            self.ui.load_path(source, 'Dados')
        self.assertEqual(self.ui.flow_var.get(), 'Fluxo UF Venda')
        self.assertTrue(self.ui.export_button.instate(['disabled']))
        self.ui.set_reference(reference)
        self.assertEqual(self.ui.session.source, source.resolve())
        self.assertTrue(self.ui.export_button.instate(['!disabled']))
        self.assertFalse(source.with_suffix('.csv').exists())

    def test_update_file_is_recognized_in_sale_mode_without_reference(self):
        from uuid import uuid4
        folder = Path.cwd() / 'work' / ('recognition_' + uuid4().hex)
        folder.mkdir(parents=True)
        source = folder / 'atualizacao.xlsx'
        fixture(source, [BASE])
        self.ui.flow_var.set('Fluxo UF Venda')
        self.ui.change_flow()
        self.ui.load_path(source, 'Dados')
        self.assertEqual(self.ui.flow_var.get(), 'Atualização de placas')
        self.assertEqual(len(self.ui.session.rows), 1)


if __name__ == '__main__':
    unittest.main()
