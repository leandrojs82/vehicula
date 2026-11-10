import zipfile
from xml.sax.saxutils import escape

def fixture(path, rows, headers=None, extra_sheet=False, numeric=False, formula=False, typed_date=False, cached_formula=False, typed_date_column=10, error_column=None, numeric_cells=None, epoch_1904=False):
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
            if numeric_cells and (rn, cn) in numeric_cells:
                cells.append(f'<c r="{ref}"><v>{numeric_cells[(rn, cn)]}</v></c>')
            elif rn == 2 and cn == error_column:
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
        properties = '<workbookPr date1904="1"/>' if epoch_1904 else ''
        z.writestr('xl/workbook.xml', f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">{properties}<sheets>{sheets}</sheets></workbook>')
        rel = '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        for n in range(1, 3 if extra_sheet else 2):
            rel += f'<Relationship Id="rId{n}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{n}.xml"/>'
            z.writestr(f'xl/worksheets/sheet{n}.xml', sheet)
        rel += '<Relationship Id="style" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'
        z.writestr('xl/_rels/workbook.xml.rels', rel)
        z.writestr('xl/styles.xml', f'<styleSheet xmlns="{ns}"><numFmts count="1"><numFmt numFmtId="164" formatCode="00000000000"/></numFmts><fonts count="1"><font/></fonts><fills count="1"><fill><patternFill patternType="none"/></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf/></cellStyleXfs><cellXfs count="3"><xf numFmtId="0"/><xf numFmtId="164" applyNumberFormat="1"/><xf numFmtId="14" applyNumberFormat="1"/></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>')



