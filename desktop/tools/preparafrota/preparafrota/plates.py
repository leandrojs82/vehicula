"""Validação apenas do formato brasileiro, sem consultar cadastro de veículos."""
import re


def plate_format(value):
    text = value.strip()
    if re.fullmatch(r'[A-Za-z]{3}-?[0-9]{4}', text):
        return 'Antiga'
    if re.fullmatch(r'[A-Za-z]{3}-?[0-9][A-Za-z][0-9]{2}', text):
        return 'Mercosul'
    return None
