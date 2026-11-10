import csv
from datetime import datetime
import hashlib
import importlib.util
import sys
import unittest
import zipfile
import uuid
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT if (ROOT / 'preparafrota.py').exists() else ROOT / 'outputs' / 'preparafrota'
sys.path.insert(0, str(APP_DIR))
spec = importlib.util.find_spec('preparafrota')
if spec:
    import preparafrota as app
else:
    app = None

HEADERS = ['Empresa', 'Produto', 'numero_renavam', 'placa_veiculo',
           'numero_chassis_veiculo', 'UF_Placa', 'veiculo_situacao',
           'Tipo consulta', 'Movimentação', 'DATA BASE']
BASE = [' Empresa, "Sul"\nMatriz ', 'Plano', '00123456789', 'ABC1D23',
        '9BWZZZ377VT004251', 'SP', 'Ativo', 'Completa', 'Incluir Consulta', '09/11/2026']


def fixture(path, rows, headers=None, extra_sheet=False, numeric=False, formula=False, typed_date=False, cached_formula=False, typed_date_column=10, error_column=None):
    """Small OOXML fixture independent of the converter's reading library."""
    def col(n):
        s = ''
        while n:
            n, v = divmod(n - 1, 26)
            s = chr(65 + v) + s
        return s
    xml_rows = []
    for rn, row in enumerate([headers or HEADERS] + rows, 1):
        cells = []
        for cn, value in enumerate(row, 1):
            ref = f'{col(cn)}{rn}'
            if value is None:
                continue
            if rn == 2 and cn == error_column:
                cells.append(f'<c r="{ref}" t="e"><v>#N/A</v></c>')
            elif numeric and rn == 2 and cn == 3:
                cells.append(f'<c r="{ref}" s="1"><v>123456789</v></c>')
            elif typed_date and rn == 2 and cn == typed_date_column:
                cells.append(f'<c r="{ref}" s="2"><v>46335</v></c>')
            elif cached_formula and rn == 2 and cn == 1:
                cells.append(f'<c r="{ref}"><f>1+1</f><v>2</v></c>')
            elif formula and rn == 2 and cn == 1:
                cells.append(f'<c r="{ref}"><f>1+1</f></c>')
            else:
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{escape(str(value))}</t></is></c>')
        xml_rows.append(f'<row r="{rn}">{"".join(cells)}</row>')
    ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    sheet = f'<worksheet xmlns="{ns}"><sheetData>{"".join(xml_rows)}</sheetData></worksheet>'
    sheets = '<sheet name="Dados" sheetId="1" r:id="rId1"/>'
    if extra_sheet:
        sheets += '<sheet name="Outra" sheetId="2" r:id="rId2"/>'
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/></Types>')
        z.writestr('_rels/.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr('xl/workbook.xml', f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>{sheets}</sheets></workbook>')
        rel = '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        for n in range(1, 3 if extra_sheet else 2):
            rel += f'<Relationship Id="rId{n}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{n}.xml"/>'
            z.writestr(f'xl/worksheets/sheet{n}.xml', sheet)
        rel += '<Relationship Id="style" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'
        z.writestr('xl/_rels/workbook.xml.rels', rel)
        z.writestr('xl/styles.xml', f'<styleSheet xmlns="{ns}"><numFmts count="1"><numFmt numFmtId="164" formatCode="00000000000"/></numFmts><fonts count="1"><font/></fonts><fills count="1"><fill><patternFill patternType="none"/></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf/></cellStyleXfs><cellXfs count="3"><xf numFmtId="0"/><xf numFmtId="164" applyNumberFormat="1"/><xf numFmtId="14" applyNumberFormat="1"/></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>')


class Conversion(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(app, 'O conversor ainda precisa ser implementado')
        # mode 0o700 de TemporaryDirectory interfere com ACLs neste ambiente Windows.
        folder = Path.cwd() / 'work' / ('test_' + uuid.uuid4().hex)
        folder.mkdir(parents=True)
        self.tmp = type('TestFolder', (), {'name': str(folder)})()
        self.source = Path(self.tmp.name) / 'Atualização de placas PreparaFrota 09-11-2026.xlsx'

    def run_file(self, rows, **kwargs):
        fixture(self.source, rows, **kwargs)
        result = app.process(self.source)
        with result['csv'].open(encoding='utf-8-sig', newline='') as f:
            return result, list(csv.reader(f))

    def test_mapping_order_and_exact_preservation(self):
        rows = []
        for movement in ['Incluir Consulta', 'Manter Consulta', 'Desativar', 'Revisar']:
            row = BASE.copy()
            row[8] = movement
            rows.append(row)
        result, out = self.run_file(rows)
        self.assertEqual(out[0], ['placa_veiculo', 'numero_chassis_veiculo', 'numero_renavam', 'empresa', 'uf_placa', 'veiculo_situacao', 'tipo consulta', 'movimentação', 'data base', 'cnpj', 'uf_venda'])
        self.assertEqual([r[7] for r in out[1:]], ['Inclusao', 'Inclusao', 'Exclusao', 'Revisar'])
        self.assertEqual(out[1], ['ABC1D23', '9BWZZZ377VT004251', '00123456789', ' Empresa, "Sul"\nMatriz ', 'SP', 'Ativo', 'Completa', 'Inclusao', '09/11/2026', '10215988000240', ''])
        self.assertEqual(len(out), 5)
        self.assertTrue(any(i['coluna'] == 'Movimentação' and i['valor'] == 'Revisar' for i in result['issues']))
        self.assertIn('<html', result['report'].read_text(encoding='utf-8'))

    def test_blank_internal_rows_block_then_can_be_corrected_without_dropping_rows(self):
        fixture(self.source, [BASE, [None] * 10, BASE])
        with self.assertRaises(ValueError):
            app.process(self.source)
        self.assertFalse(self.source.with_suffix('.csv').exists())
        session = app.prepare_session(self.source)
        self.assertEqual(len(session.pending()), 10)
        for name, value in zip(HEADERS, BASE):
            session.correct(3, name, value)
        result = app.export_session(session)
        with result['csv'].open(encoding='utf-8-sig', newline='') as f:
            out = list(csv.reader(f))
        self.assertEqual(len(out), 4)
        self.assertEqual(out[1], out[2])
        self.assertEqual(out[2], out[3])
        self.assertTrue(any('duplicad' in i['motivo'].lower() for i in result['issues']))

    def test_zero_mask_is_preserved(self):
        _, out = self.run_file([BASE], numeric=True)
        self.assertEqual(out[1][2], '00123456789')

    def test_unexpected_or_missing_or_duplicate_headers_block_export(self):
        for headers in [HEADERS + ['Nova'], HEADERS[:-1], HEADERS + ['Empresa']]:
            with self.subTest(headers=headers):
                fixture(self.source, [BASE], headers=headers)
                with self.assertRaises(ValueError):
                    app.process(self.source)
                self.assertFalse(self.source.with_suffix('.csv').exists())

    def test_ambiguous_sheets_and_missing_formula_cache_block(self):
        fixture(self.source, [BASE], extra_sheet=True)
        with self.assertRaises(ValueError):
            app.process(self.source)
        result = app.process(self.source, sheet='Dados')
        self.assertEqual(result['rows'], 1)
        fixture(self.source, [BASE], formula=True)
        with self.assertRaises(ValueError):
            app.process(self.source, output=Path(self.tmp.name) / 'formula.csv')

    def test_rare_values_and_formats_reported_without_changes(self):
        rows = []
        for n in range(20):
            row = BASE.copy()
            row[6] = 'Ativo' if n < 19 else '<Raro>'
            row[3] = f'ABC{n:04d}' if n < 19 else '???'
            rows.append(row)
        result, out = self.run_file(rows)
        self.assertEqual(out[-1][5], '<Raro>')
        self.assertEqual(out[-1][0], '???')
        self.assertTrue(any('raro' in i['motivo'].lower() for i in result['issues']))
        self.assertTrue(any('padrão' in i['motivo'].lower() for i in result['issues']))
        self.assertIn('&lt;Raro&gt;', result['report'].read_text(encoding='utf-8'))

    def test_existing_outputs_not_overwritten(self):
        fixture(self.source, [BASE])
        first = app.process(self.source)
        before = first['csv'].read_bytes()
        second = app.process(self.source)
        self.assertNotEqual(first['csv'], second['csv'])
        self.assertEqual(first['csv'].read_bytes(), before)

    def test_excel_dates_and_cached_formulas_keep_values(self):
        result, out = self.run_file([BASE], typed_date=True, cached_formula=True)
        self.assertEqual(out[1][8], '09/11/2026')
        self.assertEqual(out[1][3], '2')
        self.assertTrue(any('Fórmula' in i['motivo'] for i in result['issues']))

    def test_cli_delimiter_source_unchanged_and_csv_bom(self):
        fixture(self.source, [BASE])
        before = hashlib.sha256(self.source.read_bytes()).digest()
        run = subprocess.run([sys.executable, str(APP_DIR / 'preparafrota.py'), str(self.source), '--separador', ';'], capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).digest(), before)
        saved = self.source.with_suffix('.csv')
        self.assertTrue(saved.read_bytes().startswith(b'\xef\xbb\xbf'))
        with saved.open(encoding='utf-8-sig', newline='') as f:
            data = list(csv.reader(f, delimiter=';'))
        self.assertEqual(data[1][3], BASE[0])

    def test_date_month_minutes_and_literal_case(self):
        value = datetime(2026, 11, 4, 14, 25, 36)
        self.assertEqual(app.date_text(value, 'hh:mm dd/mm/yyyy'), '14:25 04/11/2026')
        self.assertEqual(app.date_text(value, 'mm:ss'), '25:36')
        self.assertEqual(app.date_text(value, 'dd "DE" mm "DE" yyyy'), '04 DE 11 DE 2026')

    def test_whitespace_blocks_before_any_output_and_bulk_fill_preserves_other_cells(self):
        first, second = BASE.copy(), BASE.copy()
        first[5], second[5] = '  ', ''
        fixture(self.source, [first, second, BASE])
        before = self.source.read_bytes()
        with self.assertRaises(ValueError):
            app.process(self.source)
        self.assertEqual(list(self.source.parent.glob('*.csv')), [])
        self.assertEqual(list(self.source.parent.glob('*.html')), [])
        session = app.prepare_session(self.source)
        self.assertEqual([(p['linha'], p['coluna']) for p in session.pending()], [(2, 'UF_Placa'), (3, 'UF_Placa')])
        with self.assertRaises(ValueError):
            app.export_session(session)
        self.assertEqual(session.correct(2, 'UF_Placa', 'RJ', all_empty=True), 2)
        self.assertEqual(session.pending(), [])
        result = app.export_session(session)
        with result['csv'].open(encoding='utf-8-sig', newline='') as f:
            out = list(csv.reader(f))
        self.assertEqual([r[4] for r in out[1:]], ['RJ', 'RJ', 'SP'])
        self.assertEqual(out[1][3], BASE[0])
        self.assertEqual(out[1][-1], '')
        self.assertEqual(self.source.read_bytes(), before)
        self.assertIn('RJ', result['report'].read_text(encoding='utf-8'))

    def test_text_dates_normalize_and_invalid_dates_require_correction(self):
        rows = []
        for value in ['2026-11-09', '9/11/2026', '09-11-2026', '2026-11-09 00:00:00', '31/02/2026']:
            row = BASE.copy()
            row[-1] = value
            rows.append(row)
        fixture(self.source, rows)
        session = app.prepare_session(self.source)
        self.assertEqual([(p['linha'], p['coluna']) for p in session.pending()], [(6, 'DATA BASE')])
        with self.assertRaises(ValueError):
            app.export_session(session)
        session.correct(6, 'DATA BASE', '2026-11-09')
        result = app.export_session(session)
        with result['csv'].open(encoding='utf-8-sig', newline='') as f:
            data = list(csv.reader(f))
        self.assertEqual([r[8] for r in data[1:]], ['09/11/2026'] * 5)

    def test_deleted_product_is_checked_when_present_and_generated_fields_cannot_be_edited(self):
        row = BASE.copy()
        row[1] = ''
        fixture(self.source, [row])
        session = app.prepare_session(self.source)
        self.assertEqual(session.pending()[0]['coluna'], 'Produto')
        with self.assertRaises(ValueError):
            session.correct(2, 'cnpj', 'outro')
        session.correct(2, 'Produto', 'Plano')
        self.assertEqual(session.pending(), [])

    def test_movement_changes_limit_fifty_skip_unchanged_and_preserve_original_order(self):
        rows = []
        for n in range(65):
            row = BASE.copy()
            row[3] = f'ABC{n:04d}'
            row[8] = ['Incluir Consulta', 'Manter Consulta', 'Desativar'][n % 3]
            rows.append(row)
        unchanged = BASE.copy()
        unchanged[8] = 'Revisar'
        rows.insert(1, unchanged)
        fixture(self.source, rows)
        session = app.prepare_session(self.source)
        original = [dict(record) for _, record in session.rows]
        changes = session.movement_changes()
        self.assertEqual(len(changes), 50)
        self.assertEqual(changes[0], {'linha': 2, 'placa': 'ABC0000', 'antes': 'Incluir Consulta', 'depois': 'Inclusao'})
        self.assertEqual(changes[1]['linha'], 4)
        self.assertEqual(changes[1]['antes'], 'Manter Consulta')
        self.assertEqual(changes[2]['depois'], 'Exclusao')
        self.assertEqual(changes[-1]['linha'], 52)
        self.assertEqual(len(session.movement_changes(limit=None)), 65)
        self.assertEqual([record for _, record in session.rows], original)

    def test_movement_before_value_survives_manual_corrections_and_small_files(self):
        row = BASE.copy()
        row[8] = 'Revisar'
        fixture(self.source, [row, BASE])
        session = app.prepare_session(self.source)
        session.correct(2, 'Movimentação', 'Desativar')
        self.assertEqual(session.movement_changes()[0], {'linha': 2, 'placa': 'ABC1D23', 'antes': 'Revisar', 'depois': 'Exclusao'})
        session.correct(2, 'Movimentação', 'Revisar')
        self.assertEqual(len(session.movement_changes()), 1)


if __name__ == '__main__':
    unittest.main()
