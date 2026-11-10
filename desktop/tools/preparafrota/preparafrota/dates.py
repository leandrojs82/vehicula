"""Datas textuais e números de série, respeitando o calendário do Excel."""
import re
from datetime import date, datetime
from decimal import Decimal, ROUND_FLOOR
import pandas as pd
from openpyxl.utils.datetime import from_excel, CALENDAR_WINDOWS_1900
from .errors import AppError


def normalize_date(value, epoch=CALENDAR_WINDOWS_1900):
    if isinstance(value, (datetime, date)):
        return value.strftime('%d/%m/%Y')
    text = str(value).strip()
    if re.fullmatch(r'[+-]?\d+(?:[.,]\d+)?', text):
        serial = Decimal(text.replace(',', '.'))
        minimum = 1 if epoch == CALENDAR_WINDOWS_1900 else 0
        maximum_day = (datetime.max.date() - epoch.date()).days
        if not minimum <= serial < maximum_day + 1:
            raise AppError('Número de série fora do intervalo válido de datas do Excel: ' + text)
        day = int(serial.to_integral_value(rounding=ROUND_FLOOR))
        if epoch == CALENDAR_WINDOWS_1900 and day == 60:
            raise AppError('O número 60 representa 29/02/1900 no Excel, uma data inexistente.')
        # A fração é o horário. Removê-la antes evita arredondar para outro dia.
        if day == 0:
            return epoch.strftime('%d/%m/%Y')
        try:
            return from_excel(day, epoch=epoch).strftime('%d/%m/%Y')
        except (ValueError, OverflowError, AttributeError) as exc:
            raise AppError('Não foi possível converter o número de série do Excel: ' + text) from exc
    # Restringir a forma antes do pandas evita interpretar números como épocas.
    if re.fullmatch(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}([ T]\d{1,2}:\d{2}(:\d{2}(\.\d+)?)?)?', text):
        base = text.replace('/', '-').replace('T', ' ')
        patterns = ('%Y-%m-%d', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f')
    elif re.fullmatch(r'\d{1,2}[/.-]\d{1,2}[/.-]\d{4}( \d{1,2}:\d{2}(:\d{2}(\.\d+)?)?)?', text):
        date_part, space, clock = text.partition(' ')
        base = re.sub(r'[.-]', '/', date_part) + (space + clock if space else '')
        patterns = ('%d/%m/%Y', '%d/%m/%Y %H:%M', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M:%S.%f')
    else:
        raise AppError('Informe uma data válida em DD/MM/AAAA, com ano de quatro dígitos.')
    for pattern in patterns:
        parsed = pd.to_datetime(base, format=pattern, errors='coerce', exact=True)
        if pd.notna(parsed):
            return parsed.strftime('%d/%m/%Y')
    raise AppError('Data inválida: ' + text + '. Informe DD/MM/AAAA.')
