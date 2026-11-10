"""Leitura somente: valores de XLSX e CSV, cabeçalhos e identificadores."""
import csv
import re
import unicodedata
from contextlib import ExitStack
from datetime import date, datetime
from pathlib import Path
from zipfile import BadZipFile
from xml.etree.ElementTree import ParseError
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from .constants import IDENTIFIERS, LOOKUP_FIELDS
from .errors import AppError, SheetRequired
from .models import Issue, Row, Table


def header_name(value):
    if not isinstance(value, str) or not value.strip():
        raise AppError('A primeira linha deve conter os cabeçalhos, sem colunas sem nome.')
    return unicodedata.normalize('NFC', value.strip()).casefold()


def check_headers(raw):
    names = tuple(header_name(value) for value in raw)
    if not names:
        raise AppError('O arquivo não contém cabeçalhos na primeira linha.')
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise AppError('Cabeçalhos duplicados: ' + ', '.join(duplicates))
    return names


def _cell_value(cell, cached, column, issues, source):
    value = cell.value
    if cell.data_type == 'f':
        value = cached.value
        issues.append(Issue(cell.row, column, '' if value is None else str(value),
                            'Fórmula sem resultado salvo.' if value is None else 'Fórmula lida pelo resultado salvo; confira se está atualizado.',
                            value is None, source))
    if value is None:
        return ''
    if cell.data_type == 'e' or cached.data_type == 'e':
        issues.append(Issue(cell.row, column, str(value), 'Erro de célula do Excel.', True, source))
    if isinstance(value, (date, datetime)):
        return value
    if isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    if isinstance(value, (int, float)):
        if column in IDENTIFIERS and (not float(value).is_integer() or cell.number_format not in ('General', '@') and not re.fullmatch('0+', cell.number_format)):
            raise AppError(f'{cell.coordinate}: identificador com formato numérico não suportado. Converta essa célula em texto no Excel.')
        text = str(int(value)) if float(value).is_integer() else str(value)
        if re.fullmatch('0+', cell.number_format) and float(value).is_integer():
            text = text.zfill(len(cell.number_format))
        if column in IDENTIFIERS and len(str(abs(int(value)))) >= 16:
            issues.append(Issue(cell.row, column, text, 'Identificador numérico longo: confira possível perda de precisão na origem.', False, source))
        return text
    return str(value)


def read_xlsx(path, sheet=None, fields=None):
    path = Path(path).resolve()
    if not path.is_file():
        raise AppError('Arquivo não encontrado: ' + str(path))
    if path.suffix.lower() != '.xlsx':
        raise AppError('Selecione um arquivo Excel .xlsx.')
    formulas = values = None
    streams = ExitStack()
    try:
        original_stream = streams.enter_context(path.open('rb'))
        cached_stream = streams.enter_context(path.open('rb'))
        formulas = load_workbook(original_stream, read_only=True, data_only=False)
        values = load_workbook(cached_stream, read_only=True, data_only=True)
        if sheet is None:
            if len(formulas.sheetnames) != 1:
                raise SheetRequired(path, formulas.sheetnames)
            sheet = formulas.sheetnames[0]
        if sheet not in formulas.sheetnames:
            raise AppError('Aba não encontrada: ' + sheet)
        original, cached = formulas[sheet], values[sheet]
        original.reset_dimensions()
        cached.reset_dimensions()
        originals, caches = original.iter_rows(), cached.iter_rows()
        raw = [cell.value for cell in next(originals, ())]
        next(caches, ())
        while raw and raw[-1] is None:
            raw.pop()
        headers = check_headers(raw)
        if fields and not set(fields) <= set(headers):
            raise AppError('Colunas ausentes na referência: ' + ', '.join(sorted(set(fields) - set(headers))))
        issues, rows, empty_rows = [], [], []
        for number, (cells, saved) in enumerate(zip(originals, caches), 2):
            if any(cell.value is not None for cell in cells[len(headers):]):
                raise AppError(f'Linha {number}: há dados em uma coluna sem cabeçalho.')
            record = {}
            for index, name in enumerate(headers):
                if fields and name not in fields:
                    continue
                record[name] = _cell_value(cells[index], saved[index], name, issues, str(path)) if index < len(cells) else ''
            row = Row(number, record)
            if all(cell.value is None for cell in cells):
                empty_rows.append(row)
            else:
                rows.extend(empty_rows)
                empty_rows.clear()
                rows.append(row)
        return Table(path, sheet, headers, rows, issues, formulas.epoch)
    except (AppError, SheetRequired):
        raise
    except PermissionError as exc:
        raise AppError('Sem acesso ao arquivo. Feche-o em outros programas e tente novamente.') from exc
    except (OSError, BadZipFile, InvalidFileException, ValueError, KeyError, ParseError) as exc:
        raise AppError('Não foi possível ler o Excel: ' + str(exc)) from exc
    finally:
        for workbook in (formulas, values):
            if workbook is not None:
                workbook.close()
        streams.close()


def read_reference_csv(path):
    path = Path(path).resolve()
    if not path.is_file():
        raise AppError('Arquivo não encontrado: ' + str(path))
    try:
        with path.open(encoding='utf-8-sig', newline='') as stream:
            first = stream.readline()
            selected = None
            for separator in (';', ',', '\t'):
                raw = next(csv.reader([first], delimiter=separator))
                names = tuple(header_name(name) for name in raw)
                if set(LOOKUP_FIELDS) <= set(names):
                    selected = separator
                    headers = check_headers(raw)
                    break
            if selected is None:
                raise AppError('O CSV de referência precisa conter placa_veiculo, veiculo_situacao e tipo consulta.')
            rows = []
            for number, values in enumerate(csv.reader(stream, delimiter=selected, strict=True), 2):
                if not values:
                    continue
                if len(values) != len(headers):
                    raise AppError(f'Registro {number} do CSV: número de campos incompatível.')
                rows.append(Row(number, {name: values[headers.index(name)] for name in LOOKUP_FIELDS}))
            return Table(path, 'CSV', headers, rows)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise AppError('Não foi possível ler o CSV de referência: ' + str(exc)) from exc
