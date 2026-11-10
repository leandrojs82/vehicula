"""Saída única padronizada, com proteção de arquivos existentes."""
import csv
import html
from pathlib import Path
from .constants import COLUMNS
from .errors import AppError, PendingError
from .models import ExportResult
from .validation import pending, warnings


def _table(headers, rows):
    esc = lambda value: html.escape(str(value))
    return '<table><tr>' + ''.join('<th>' + esc(v) + '</th>' for v in headers) + '</tr>' + ''.join('<tr>' + ''.join('<td>' + esc(v) + '</td>' for v in row) + '</tr>' for row in rows) + '</table>'


def render_report(session):
    esc = lambda value: html.escape(str(value))
    alerts = warnings(session)
    output = '<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Conferência PreparaFrota</title><style>body{font:15px system-ui;margin:32px;color:#20313b}table{border-collapse:collapse;width:100%;margin:16px 0}td,th{border:1px solid #cbd5db;padding:8px;text-align:left;white-space:pre-wrap;overflow-wrap:anywhere}th{background:#edf3f5}</style><h1>Conferência PreparaFrota</h1>'
    output += '<p>Arquivo: ' + esc(session.source) + '. Aba: ' + esc(session.sheet) + f'. Registros: {len(session.rows)}.</p><p>CSV com 11 cabeçalhos em minúsculas, ponto e vírgula e UTF-8 com BOM. Datas convertíveis em DD/MM/AAAA. Valores confirmados como estão são preservados e registrados abaixo. Arquivos de origem preservados.</p>'
    output += '<h2>Ajustes</h2>' + (_table(['Linha', 'Coluna', 'Antes', 'Depois'], [(c.row, c.column, c.before, c.after) for c in session.changes]) if session.changes else '<p>Sem ajustes manuais ou de formato de data.</p>')
    if session.confirmations:
        output += '<h2>Confirmado como está</h2>' + _table(['Linha', 'Campo', 'Valor mantido', 'Pendência aceita pelo usuário'], [(c.row, c.column, c.value, c.reason) for c in session.confirmations.values()])
    output += '<h2>Validação de placas</h2><p>São aceitos os formatos brasileiro antigo e Mercosul, com hífen opcional e sem alterar a placa exportada. A conferência é de formato, sem consulta cadastral externa. Os demais avisos foram desativados.</p>'
    output += _table(['Linha', 'Coluna', 'Valor', 'Aviso'], [(i.row, i.column, i.value, i.reason) for i in alerts]) if alerts else '<p>Nenhum aviso pelos critérios utilizados.</p>'
    if session.flow == 'venda':
        output += '<h2>Cruzamento por placa</h2><p>Referência: ' + esc(session.reference.label if session.reference else 'Confirmação manual sem referência') + '</p>'
        output += _table(['Linha venda', 'Placa', 'Resultado', 'Arquivo consultado', 'Registros na referência', 'Situação', 'Tipo consulta'], [(row.number, row.values['placa_veiculo'], session.matches[row.number].status, session.matches[row.number].source_label, ', '.join(str(n) for candidate in session.matches[row.number].candidates for n in candidate.lines), row.values['veiculo_situacao'], row.values['tipo consulta']) for row in session.rows])
        if session.supplemental_references:
            output += '<h2>Consultas complementares</h2>' + _table(['Arquivo'], [(reference.label,) for reference in session.supplemental_references])
        references = ([session.reference] if session.reference else []) + session.supplemental_references
        errors = [(reference.label, issue) for reference in references for issue in reference.issues if issue.blocking]
        if errors:
            output += '<h2>Erros na origem do cruzamento</h2>' + _table(['Arquivo', 'Linha referência', 'Coluna', 'Valor', 'Erro'], [(label, i.row, i.column, i.value, i.reason) for label, i in errors])
    return output + '</html>'


def export_csv(session, destination=None):
    blocked = pending(session)
    if blocked:
        detail = '\n'.join(f'Linha {i.row}, {i.column}: {i.reason}' for i in blocked[:20])
        raise PendingError(f'{len(blocked)} pendência(s). Nenhum arquivo foi gerado.\n{detail}')
    destination = Path(destination).resolve() if destination else session.source.with_suffix('.csv')
    if destination.suffix.lower() != '.csv':
        raise AppError('A saída deve ser um arquivo .csv.')
    base, number = destination, 1
    report = destination.with_name(destination.stem + '_conferencia.html')
    while destination.exists() or report.exists():
        number += 1
        destination = base.with_name(f'{base.stem}_{number}.csv')
        report = destination.with_name(destination.stem + '_conferencia.html')
    report_text = render_report(session)
    created = []
    try:
        with destination.open('x', encoding='utf-8-sig', newline='') as stream:
            created.append(destination)
            writer = csv.writer(stream, delimiter=';')
            writer.writerow(COLUMNS)
            writer.writerows([row.values[name] for name in COLUMNS] for row in session.rows)
        with report.open('x', encoding='utf-8') as stream:
            created.append(report)
            stream.write(report_text)
    except (OSError, UnicodeError, csv.Error) as exc:
        for path in created:
            path.unlink(missing_ok=True)
        raise AppError('Não foi possível salvar a saída. Verifique a pasta e se o arquivo está aberto. ' + str(exc)) from exc
    return ExportResult(destination, report, len(session.rows))
