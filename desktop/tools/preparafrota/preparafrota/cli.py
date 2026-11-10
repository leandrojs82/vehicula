"""Entrada de console com as mesmas regras usadas pela interface."""
import argparse
import logging
from .errors import AppError, PendingError
from .processor import load_session
from .exporter import export_csv


def main(argv=None):
    parser = argparse.ArgumentParser(description='PreparaFrota: XLSX para CSV com ponto e vírgula e UTF-8 com BOM.')
    parser.add_argument('arquivo', nargs='?')
    parser.add_argument('--referencia', help='Atualização de placas, em XLSX ou CSV')
    parser.add_argument('--aba')
    parser.add_argument('--aba-referencia')
    parser.add_argument('--saida')
    args = parser.parse_args(argv)
    if args.arquivo is None:
        from .ui import run
        return run()
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    try:
        session = load_session(args.arquivo, args.referencia, args.aba, args.aba_referencia)
        result = export_csv(session, args.saida)
        print(f'{result.rows} registros exportados.\nCSV: {result.csv}\nConferência: {result.report}')
        return 0
    except PendingError as exc:
        logging.error('Erro: %s\nAbra a interface para revisar as pendências.', exc)
        return 3
    except AppError as exc:
        logging.error('Erro: %s', exc)
        return 2
