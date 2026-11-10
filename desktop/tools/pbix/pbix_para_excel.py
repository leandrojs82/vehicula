"""
Converte as tabelas de um arquivo do Power BI (.pbix) em Excel.

O .pbix guarda os dados num modelo compactado (VertiPaq). A biblioteca pbixray lê esse modelo
sem precisar do Power BI instalado. Só funciona com dados importados: tabela em DirectQuery
não tem dados dentro do arquivo.

Uso:
    python pbix_para_excel.py ARQUIVO.pbix --listar
    python pbix_para_excel.py ARQUIVO.pbix
    python pbix_para_excel.py ARQUIVO.pbix --tabelas "Autuação sem Multa" "Antecipação"
    python pbix_para_excel.py ARQUIVO.pbix --um-arquivo --texto
    python pbix_para_excel.py ARQUIVO.pbix --csv --saida C:\\pasta

Padrão: um .xlsx por tabela, na pasta "<nome do pbix>_excel" ao lado do arquivo. As tabelas
de data que o Power BI cria sozinho (DateTableTemplate_..., LocalDateTable_...) ficam de fora.
"""

import argparse
import re
import sys
import time
import unicodedata
from pathlib import Path

import pandas as pd
from pbixray import PBIXRay

LIMITE_LINHAS_EXCEL = 1_048_575  # 1.048.576 linhas por aba, menos o cabeçalho
PREFIXOS_AUTOMATICOS = ("DateTableTemplate_", "LocalDateTable_")


def nome_de_arquivo(texto):
    """Nome sem acento e sem caractere proibido no Windows: 'Autuação sem Multa' -> 'autuacao_sem_multa'."""
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^\w\-]+", "_", texto).strip("_").lower()
    return texto or "tabela"


def nome_de_aba(texto, usados):
    """Aba do Excel: até 31 caracteres, sem []:*?/\\ e sem repetir."""
    base = re.sub(r"[\[\]:*?/\\]", "_", texto)[:31] or "Tabela"
    nome, n = base, 2
    while nome.lower() in usados:
        sufixo = f" ({n})"
        nome = base[: 31 - len(sufixo)] + sufixo
        n += 1
    usados.add(nome.lower())
    return nome


def preparar(df, texto):
    """Ajusta o DataFrame para o Excel aceitar."""
    for coluna in df.columns:
        serie = df[coluna]
        # O Excel não aceita data com fuso horário
        if isinstance(serie.dtype, pd.DatetimeTZDtype):
            df[coluna] = serie.dt.tz_localize(None)
    if texto:
        # Tudo como texto: o Excel não vira renavam/AIT em número nem come zero à esquerda
        df = df.astype("string")
    return df


def partes(df):
    """Fatias de até LIMITE_LINHAS_EXCEL linhas (uma só, na maioria das tabelas)."""
    if len(df) <= LIMITE_LINHAS_EXCEL:
        return [df]
    return [df.iloc[i:i + LIMITE_LINHAS_EXCEL] for i in range(0, len(df), LIMITE_LINHAS_EXCEL)]


def motor_excel():
    try:
        import xlsxwriter  # noqa: F401  (bem mais rápido que o openpyxl em tabela grande)
        return "xlsxwriter"
    except ImportError:
        return "openpyxl"


def escolher_tabelas(modelo, pedidas, incluir_automaticas):
    todas = list(modelo.tables)
    if pedidas:
        faltando = [t for t in pedidas if t not in todas]
        if faltando:
            sys.exit(f"Tabela(s) não encontrada(s): {', '.join(faltando)}\n"
                     f"Tabelas do arquivo: {', '.join(todas)}")
        return pedidas
    if incluir_automaticas:
        return todas
    return [t for t in todas if not t.startswith(PREFIXOS_AUTOMATICOS)]


def listar(modelo):
    estatisticas = modelo.statistics
    linhas = {}
    if estatisticas is not None and "TableName" in estatisticas and "Cardinality" in estatisticas:
        # A cardinalidade da maior coluna dá uma estimativa das linhas sem carregar a tabela
        linhas = estatisticas.groupby("TableName")["Cardinality"].max().to_dict()
    print(f"{'Tabela':<45} {'Linhas (aprox.)':>16}")
    for tabela in modelo.tables:
        auto = "  (automática)" if tabela.startswith(PREFIXOS_AUTOMATICOS) else ""
        qtd = linhas.get(tabela)
        print(f"{tabela:<45} {qtd if qtd is not None else '?':>16}{auto}")


def main():
    parser = argparse.ArgumentParser(description="Converte as tabelas de um .pbix em Excel.")
    parser.add_argument("pbix", help="caminho do arquivo .pbix")
    parser.add_argument("--saida", help="pasta de saída (padrão: <nome do pbix>_excel ao lado do arquivo)")
    parser.add_argument("--tabelas", nargs="+", metavar="TABELA", help="só estas tabelas (nome como aparece no --listar)")
    parser.add_argument("--listar", action="store_true", help="só lista as tabelas do arquivo")
    parser.add_argument("--um-arquivo", action="store_true", help="um .xlsx só, com uma aba por tabela")
    parser.add_argument("--texto", action="store_true", help="grava todas as colunas como texto")
    parser.add_argument("--csv", action="store_true", help="gera .csv (UTF-8 com BOM, separador ;) em vez de .xlsx")
    parser.add_argument("--incluir-automaticas", action="store_true", help="inclui as tabelas de data automáticas")
    args = parser.parse_args()

    arquivo = Path(args.pbix).expanduser().resolve()
    if not arquivo.is_file():
        sys.exit(f"Arquivo não encontrado: {arquivo}")

    print(f"Lendo {arquivo.name}...")
    modelo = PBIXRay(str(arquivo))

    if args.listar:
        listar(modelo)
        return

    tabelas = escolher_tabelas(modelo, args.tabelas, args.incluir_automaticas)
    if not tabelas:
        sys.exit("Nenhuma tabela para converter.")

    saida = Path(args.saida).expanduser().resolve() if args.saida else arquivo.parent / f"{arquivo.stem}_excel"
    saida.mkdir(parents=True, exist_ok=True)
    motor = motor_excel()

    gerados = []
    escritor_unico = None
    abas_usadas = set()
    if args.um_arquivo and not args.csv:
        destino = saida / f"{nome_de_arquivo(arquivo.stem)}.xlsx"
        escritor_unico = pd.ExcelWriter(destino, engine=motor)
        gerados.append(destino)

    try:
        for tabela in tabelas:
            inicio = time.time()
            df = preparar(modelo.get_table(tabela), args.texto)
            qtd = f"{len(df):,}".replace(",", ".")
            print(f"  {tabela}: {qtd} linhas, {len(df.columns)} colunas", end="", flush=True)

            if args.csv:
                destino = saida / f"{nome_de_arquivo(tabela)}.csv"
                df.to_csv(destino, index=False, sep=";", encoding="utf-8-sig")
                gerados.append(destino)
            elif escritor_unico is not None:
                for parte in partes(df):
                    parte.to_excel(escritor_unico, sheet_name=nome_de_aba(tabela, abas_usadas), index=False)
            else:
                destino = saida / f"{nome_de_arquivo(tabela)}.xlsx"
                with pd.ExcelWriter(destino, engine=motor) as escritor:
                    usadas = set()
                    for parte in partes(df):
                        parte.to_excel(escritor, sheet_name=nome_de_aba(tabela, usadas), index=False)
                gerados.append(destino)

            print(f" ({time.time() - inicio:.1f}s)")
            if len(df) > LIMITE_LINHAS_EXCEL and not args.csv:
                print(f"    passou do limite do Excel: dividida em {len(partes(df))} abas")
    finally:
        if escritor_unico is not None:
            print("  Gravando o arquivo...")
            escritor_unico.close()

    print(f"\nPronto. {len(gerados)} arquivo(s) em {saida}:")
    for caminho in gerados:
        print(f"  {caminho.name}")


if __name__ == "__main__":
    main()
