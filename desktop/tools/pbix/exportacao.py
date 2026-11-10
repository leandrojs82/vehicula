"""Abre modelos locais e exporta as tabelas selecionadas."""
import re
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import BadZipFile, ZipFile

import pandas as pd
from pbixray import PBIXRay
from pbixray.exceptions import NoEmbeddedModelError

from pbix_para_excel import nome_de_aba, nome_de_arquivo, partes, preparar


FORMATOS = {"unico": "excel", "separado": "excel", "csv": "csv"}
RESERVADO = re.compile(r"^(con|prn|aux|nul|com[0-9]|lpt[0-9])$", re.IGNORECASE)


def abrir_modelo(arquivo):
    if arquivo.suffix.lower() != ".pbix":
        raise ValueError("Escolha um arquivo com a extensão .pbix.")
    try:
        with ZipFile(arquivo) as pacote:
            if "DataModel" not in pacote.namelist():
                raise ValueError("Este relatório não contém um modelo com dados importados.")
        return PBIXRay(str(arquivo), on_disk=True)
    except BadZipFile as erro:
        raise ValueError("Escolha um arquivo .pbix válido. O arquivo selecionado está ilegível.") from erro
    except NoEmbeddedModelError as erro:
        raise ValueError("Este relatório não contém um modelo com dados importados.") from erro


def nome_de_saida(tabela, usados):
    base = nome_de_arquivo(tabela)[:100]
    if RESERVADO.fullmatch(base):
        base = f"tabela_{base}"
    nome, numero = base, 2
    while nome in usados:
        nome = f"{base}_{numero}"
        numero += 1
    usados.add(nome)
    return nome


def gravar_abas(escritor, tabela, dados, usadas):
    nome = tabela.strip("'")
    if nome.casefold() == "history":
        nome = "History (tabela)"
    for parte in partes(dados):
        aba = nome_de_aba(nome, usadas)
        # O Excel também rejeita apóstrofos nas pontas após truncar.
        if aba.endswith("'"):
            aba = nome_de_aba(aba.rstrip("'"), usadas)
        planilha = escritor.book.add_worksheet(aba)
        planilha.add_write_handler(str, gravar_formula_matricial_como_texto)
        parte.to_excel(escritor, sheet_name=aba, index=False)


def gravar_formula_matricial_como_texto(planilha, linha, coluna, valor, estilo=None):
    # O XlsxWriter reconhece esta sintaxe mesmo com strings_to_formulas=False.
    if valor.startswith("{=") and valor.endswith("}"):
        return planilha.write_string(linha, coluna, valor, estilo)
    return None


def escritor_excel(destino):
    return pd.ExcelWriter(destino, engine="xlsxwriter", engine_kwargs={
        "options": {"strings_to_formulas": False, "strings_to_urls": False}
    })


def exportar(modelo, arquivo, tabelas, destino, formato, como_texto, progresso=lambda *_: None):
    if not tabelas:
        raise ValueError("Selecione pelo menos uma tabela para exportar.")
    tipo = FORMATOS[formato]
    prefixo = f"{arquivo.stem[:100]}_{tipo}"
    nomes = set()

    with TemporaryDirectory(prefix=".pbix-", dir=destino) as temporaria:
        pasta = Path(temporaria) / "arquivos"
        pasta.mkdir()

        with ExitStack() as recursos:
            livro = None
            abas = set()
            if formato == "unico":
                caminho = pasta / f"{nome_de_saida(arquivo.stem, nomes)}.xlsx"
                livro = recursos.enter_context(escritor_excel(caminho))

            for indice, tabela in enumerate(tabelas, 1):
                progresso(indice, len(tabelas), tabela)
                dados = preparar(modelo.get_table(tabela), como_texto)
                if formato == "csv":
                    caminho = pasta / f"{nome_de_saida(tabela, nomes)}.csv"
                    dados.to_csv(caminho, index=False, sep=";", encoding="utf-8-sig")
                elif livro is not None:
                    gravar_abas(livro, tabela, dados, abas)
                else:
                    caminho = pasta / f"{nome_de_saida(tabela, nomes)}.xlsx"
                    with escritor_excel(caminho) as separado:
                        gravar_abas(separado, tabela, dados, set())
                del dados

        # Publica o conjunto completo de uma vez, em uma pasta própria.
        numero = 1
        while True:
            nome = prefixo if numero == 1 else f"{prefixo}_{numero}"
            resultado = destino / nome
            if not resultado.exists():
                try:
                    pasta.rename(resultado)
                    return resultado
                except FileExistsError:
                    pass
            numero += 1

