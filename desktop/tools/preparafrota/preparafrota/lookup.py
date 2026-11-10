"""Índice por placa. Repetições equivalentes nunca multiplicam a venda."""
import re
from .constants import EXCEL_ERRORS, JOIN_FIELDS, LOOKUP_FIELDS
from .errors import AppError
from .models import Candidate, Reference, Match, Session
from .reader import read_xlsx, read_reference_csv


def plate_key(value):
    return re.sub(r'[\s-]+', '', value).upper()


def load_reference(source, sheet=None):
    if isinstance(source, Session):
        if source.flow != 'atualizacao':
            raise AppError('A referência deve ser a atualização de placas, não a venda.')
        rows = source.rows
        warnings = [issue for issue in source.issues if issue.column in LOOKUP_FIELDS and any(row.number == issue.row and row.values[issue.column] == issue.value for row in rows)]
        label = str(source.source) + ' (sessão revisada)'
    else:
        from pathlib import Path
        path = Path(source)
        table = read_reference_csv(path) if path.suffix.lower() == '.csv' else read_xlsx(path, sheet, LOOKUP_FIELDS)
        rows, warnings = table.rows, table.issues
        label = str(table.source) + ' / ' + table.sheet
    index = {}
    warning_rows = {}
    for warning in warnings:
        warning_rows.setdefault(warning.row, []).append(warning)
    for row in rows:
        key = plate_key(str(row.values['placa_veiculo']))
        if not key:
            continue
        situation, query = (str(row.values[name]) for name in JOIN_FIELDS)
        candidates = index.setdefault(key, [])
        candidate = next((item for item in candidates if (item.situation, item.query) == (situation, query)), None)
        if candidate is None:
            candidate = Candidate(situation, query)
            candidates.append(candidate)
        candidate.lines.append(row.number)
        candidate.issues.extend(warning_rows.get(row.number, []))
    return Reference(label, index, warnings)


def apply_lookup(session, row):
    key = plate_key(row.values['placa_veiculo'])
    candidates = session.reference.index.get(key, []) if session.reference and key else []
    label = session.reference.label if session.reference else ''
    complementary = False
    if session.reference and key and not candidates:
        for reference in session.supplemental_references:
            extra_candidates = reference.index.get(key, [])
            if extra_candidates:
                candidates, label, complementary = extra_candidates, reference.label, True
                break
    override = session.overrides.get(row.number)
    if override and override[0] == key:
        values = override[1:]
        match = Match('Confirmado manualmente', candidates, False, True)
    elif session.reference is None:
        values, match = ('', ''), Match('Selecione a atualização de referência', [], True)
    elif not key:
        values, match = ('', ''), Match('Preencha a placa', [], True)
    elif not candidates:
        values, match = ('', ''), Match('Placa não encontrada', [], True)
    elif len(candidates) > 1:
        values, match = ('', ''), Match('Dados conflitantes na referência', candidates, True)
    else:
        candidate = candidates[0]
        pair = candidate.situation, candidate.query
        if any(not value.strip() for value in pair):
            values, match = ('', ''), Match('Dados incompletos na referência', candidates, True)
        elif any(value in EXCEL_ERRORS for value in pair) or any(issue.blocking for issue in candidate.issues):
            values, match = ('', ''), Match('Erro de célula na referência', candidates, True)
        else:
            values = pair
            match = Match('Encontrado em consulta complementar' if complementary else 'Encontrado', candidates, False)
    for field, value in zip(JOIN_FIELDS, values):
        row.values[field] = value
    session.matches[row.number] = match
    match.source_label = label
