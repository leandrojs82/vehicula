"""Transformações e edições da sessão. Não depende da interface visual."""
from .constants import (COLUMNS, CNPJ, UPDATE_REQUIRED, SALE_REQUIRED,
                        SALE_RENAME, MOVEMENTS, JOIN_FIELDS, EXCEL_ERRORS)
from .dates import normalize_date
from .errors import AppError
from .models import Session, Row, Change, Confirmation
from .reader import read_xlsx
from .lookup import load_reference, apply_lookup, plate_key


def detect_flow(headers):
    names = set(headers)
    if set(UPDATE_REQUIRED) <= names <= set(UPDATE_REQUIRED) | {'produto'}:
        return 'atualizacao'
    if names == set(SALE_REQUIRED):
        return 'venda'
    expected = set(SALE_REQUIRED) if names & {'data venda', 'uf origem', 'uf venda'} else set(UPDATE_REQUIRED)
    allowed = expected if expected == set(SALE_REQUIRED) else expected | {'produto'}
    missing, extra = sorted(expected - names), sorted(names - allowed)
    raise AppError(f'Estrutura não reconhecida. Colunas ausentes: {missing}. Colunas extras: {extra}. Nenhuma coluna extra foi descartada.')


def load_session(path, reference=None, sheet=None, reference_sheet=None):
    table = read_xlsx(path, sheet)
    flow = detect_flow(table.headers)
    rows, originals, changes = [], {}, []
    for original in table.rows:
        data = {name: '' for name in COLUMNS}
        for name, value in original.values.items():
            target = SALE_RENAME.get(name, name) if flow == 'venda' else name
            if target in data:
                data[target] = value
        originals[original.number] = str(data['movimentação']) if flow == 'atualizacao' else ''
        data['movimentação'] = MOVEMENTS.get(data['movimentação'], data['movimentação']) if flow == 'atualizacao' else 'Inclusao'
        data['cnpj'] = CNPJ
        if flow == 'atualizacao':
            data['uf_venda'] = ''
        before = data['data base']
        try:
            data['data base'] = normalize_date(before, table.date_epoch)
        except AppError:
            data['data base'] = str(before)
        if str(before) != data['data base']:
            changes.append(Change(original.number, 'data base', str(before), data['data base']))
        rows.append(Row(original.number, {name: str(value) for name, value in data.items()}))
    issues = []
    for issue in table.issues:
        if issue.column == 'produto':
            continue
        if flow == 'venda':
            issue.column = SALE_RENAME.get(issue.column, issue.column)
        issues.append(issue)
    session = Session(table.source, table.sheet, flow, rows, issues, originals, changes=changes, date_epoch=table.date_epoch)
    if flow == 'venda':
        if reference is not None:
            set_reference(session, reference, reference_sheet)
        else:
            for row in rows:
                apply_lookup(session, row)
    return session


def set_reference(session, reference, sheet=None):
    if session.flow != 'venda':
        raise AppError('Somente o fluxo de venda usa uma referência.')
    candidate = load_reference(reference, sheet)
    session.reference = candidate
    session.overrides.clear()
    session.supplemental_references.clear()
    for row in session.rows:
        apply_lookup(session, row)


def edit_cell(session, number, column, value, all_empty=False):
    if column not in COLUMNS or column == 'cnpj' or (column == 'uf_venda' and session.flow == 'atualizacao') or (column == 'movimentação' and session.flow == 'venda'):
        raise AppError('Essa coluna é definida automaticamente.')
    if session.flow == 'venda' and column in JOIN_FIELDS:
        raise AppError('Confirme situação e tipo de consulta juntos no cruzamento.')
    if not isinstance(value, str) or not value.strip() or value in EXCEL_ERRORS:
        raise AppError('Informe um valor preenchido e sem erro de célula.')
    if column == 'data base':
        value = normalize_date(value, session.date_epoch)
    if column == 'movimentação' and value not in ('Inclusao', 'Exclusao'):
        raise AppError('Escolha Inclusao ou Exclusao.')
    selected = session.row(number)
    if all_empty and selected.values[column].strip():
        raise AppError('Para preencher os vazios da coluna, selecione uma célula vazia.')
    rows = [row for row in session.rows if not row.values[column].strip()] if all_empty else [selected]
    count = 0
    for row in rows:
        previous = row.values[column]
        if previous != value:
            row.values[column] = value
            session.changes.append(Change(row.number, column, previous, value))
            session.confirmations.pop((row.number, column), None)
            count += 1
            if session.flow == 'venda' and column == 'placa_veiculo':
                session.overrides.pop(row.number, None)
                apply_lookup(session, row)
    return count


def resolve_lookup(session, number, situation, query):
    if session.flow != 'venda':
        raise AppError('O cruzamento pertence ao fluxo de venda.')
    if not all(isinstance(value, str) and value.strip() and value not in EXCEL_ERRORS for value in (situation, query)):
        raise AppError('Informe situação e tipo de consulta válidos antes de confirmar.')
    row = session.row(number)
    key = plate_key(row.values['placa_veiculo'])
    accepted_plate = session.confirmations.get((number, 'placa_veiculo'))
    if not key and not (accepted_plate and accepted_plate.value == row.values['placa_veiculo']):
        raise AppError('Preencha a placa ou confirme explicitamente seu valor atual em Pendências antes de informar o par manual.')
    for column, value in zip(JOIN_FIELDS, (situation, query)):
        session.changes.append(Change(number, column, row.values[column], value))
    session.overrides[number] = (key, situation, query)
    apply_lookup(session, row)


def movement_preview(session, limit=50):
    changed = [dict(linha=row.number, placa=row.values['placa_veiculo'], antes=session.original_movements[row.number], depois=row.values['movimentação'])
               for row in session.rows if session.original_movements[row.number] != row.values['movimentação']]
    return changed if limit is None else changed[:limit]


def confirm_pending(session, number, column):
    from .validation import pending
    if column in ('referência', 'cruzamento') or number == 0:
        raise AppError('Para o cruzamento, consulte outro arquivo ou confirme situação e tipo de consulta juntos.')
    issue = next((item for item in pending(session) if item.row == number and item.column == column), None)
    if issue is None:
        raise AppError('Essa célula não possui uma pendência para confirmar.')
    session.confirmations[(number, column)] = Confirmation(number, column, issue.value, issue.reason)


def missing_lookup_rows(session):
    if session.flow != 'venda' or session.reference is None:
        return []
    return [row for row in session.rows
            if plate_key(row.values['placa_veiculo']) and row.number in session.matches
            and session.matches[row.number].needs_review and not session.matches[row.number].candidates]


def add_supplemental_reference(session, source, sheet=None):
    missing = missing_lookup_rows(session)
    if not missing:
        raise AppError('Não há placas sem correspondência para consultar em outro arquivo.')
    reference = load_reference(source, sheet)
    session.supplemental_references.append(reference)
    for row in missing:
        apply_lookup(session, row)
    return sum(not session.matches[row.number].needs_review for row in missing)
