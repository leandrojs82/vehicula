"""Pendências bloqueiam a saída; avisos preservam os valores para conferência."""
from .constants import COLUMNS, JOIN_FIELDS, EXCEL_ERRORS
from .dates import normalize_date
from .errors import AppError
from .models import Issue
from .plates import plate_format


def pending(session):
    result = []
    if session.flow == 'venda' and session.reference is None:
        result.append(Issue(0, 'referência', '', 'Selecione a atualização de placas usada no cruzamento.', True))
    for row in session.rows:
        match = session.matches.get(row.number)
        for column in COLUMNS:
            if session.flow == 'atualizacao' and column == 'uf_venda':
                continue
            if match and match.needs_review and column in JOIN_FIELDS:
                continue
            value = row.values[column]
            reason = ''
            if not value.strip():
                reason = 'Campo vazio. Preencha antes de exportar.'
            elif value in EXCEL_ERRORS:
                reason = 'Erro de célula. Corrija o valor antes de exportar.'
            elif column == 'movimentação' and value not in ('Inclusao', 'Exclusao'):
                reason = 'Movimentação desconhecida. Escolha Inclusao ou Exclusao.'
            elif column == 'data base':
                try:
                    normalize_date(value, session.date_epoch)
                except AppError as exc:
                    reason = 'Não foi possível converter para data: ' + str(exc)
            if reason:
                result.append(Issue(row.number, column, value, reason, True, str(session.source)))
        if match and match.needs_review and session.reference is not None:
            result.append(Issue(row.number, 'cruzamento', row.values['placa_veiculo'], match.status, True, str(session.source)))
    return [issue for issue in result
            if (issue.row, issue.column) not in session.confirmations
            or session.confirmations[(issue.row, issue.column)].value != issue.value
            or session.confirmations[(issue.row, issue.column)].reason != issue.reason]


def warnings(session):
    return [Issue(row.number, 'placa_veiculo', row.values['placa_veiculo'],
                  'Placa fora dos formatos ABC1234 (antiga) e ABC1D23 (Mercosul).', False, str(session.source))
            for row in session.rows if row.values['placa_veiculo'].strip()
            and plate_format(row.values['placa_veiculo']) is None]
