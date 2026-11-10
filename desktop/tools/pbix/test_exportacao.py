import csv
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

import exportacao


class Modelo:
    tables = ["Frota", "Frotá", "LocalDateTable_1"]

    def get_table(self, nome):
        if nome == "Com erro":
            raise ValueError("Tabela ilegível")
        return pd.DataFrame({"AIT": ["000125", "=2+2"], "Total": [3, 5],
                             "Texto": ["{=2+2}", ""]})


class ExportacaoTest(unittest.TestCase):
    def setUp(self):
        temporario = tempfile.TemporaryDirectory()
        self.addCleanup(temporario.cleanup)
        self.pasta = Path(temporario.name)
        self.arquivo = self.pasta / "Relatório.pbix"
        self.arquivo.touch()

    def test_excel_unico_preserva_texto_e_formula_literal(self):
        saida = exportacao.exportar(Modelo(), self.arquivo, ["Frota", "Frotá"],
                                   self.pasta, "unico", True)
        livro = load_workbook(saida / "relatorio.xlsx", read_only=True)
        try:
            self.assertEqual(livro.sheetnames, ["Frota", "Frotá"])
            self.assertEqual(livro["Frota"]["A2"].value, "000125")
            self.assertEqual(livro["Frota"]["A3"].data_type, "s")
            self.assertEqual(livro["Frota"]["B2"].value, "3")
            self.assertEqual(livro["Frota"]["C2"].value, "{=2+2}")
            self.assertEqual(livro["Frota"]["C2"].data_type, "s")
        finally:
            livro.close()

    def test_csv_com_bom_e_nomes_sem_colisao(self):
        saida = exportacao.exportar(Modelo(), self.arquivo, ["Frota", "Frotá"],
                                   self.pasta, "csv", False)
        self.assertEqual(sorted(p.name for p in saida.iterdir()), ["frota.csv", "frota_2.csv"])
        arquivo = saida / "frota.csv"
        self.assertTrue(arquivo.read_bytes().startswith(b"\xef\xbb\xbf"))
        with arquivo.open(encoding="utf-8-sig", newline="") as fluxo:
            self.assertEqual(list(csv.reader(fluxo, delimiter=";"))[1], ["000125", "3", "{=2+2}"])

    def test_xlsx_por_tabela_divide_abas_e_preserva_tipos(self):
        from unittest.mock import patch
        with patch("pbix_para_excel.LIMITE_LINHAS_EXCEL", 1):
            saida = exportacao.exportar(Modelo(), self.arquivo, ["Frota"],
                                       self.pasta, "separado", False)
        livro = load_workbook(saida / "frota.xlsx", read_only=True)
        try:
            self.assertEqual(livro.sheetnames, ["Frota", "Frota (2)"])
            self.assertEqual(livro["Frota"]["B2"].value, 3)
            self.assertEqual(livro["Frota (2)"]["B2"].value, 5)
        finally:
            livro.close()

    def test_falha_descarta_arquivos_da_tentativa(self):
        with self.assertRaisesRegex(ValueError, "ilegível"):
            exportacao.exportar(Modelo(), self.arquivo, ["Frota", "Com erro"],
                                self.pasta, "separado", False)
        self.assertEqual(list(self.pasta.iterdir()), [self.arquivo])

    def test_nova_exportacao_preserva_pasta_anterior(self):
        anterior = self.pasta / "Relatório_csv"
        anterior.mkdir()
        (anterior / "frota.csv").write_text("anterior")
        saida = exportacao.exportar(Modelo(), self.arquivo, ["Frota"],
                                   self.pasta, "csv", False)
        self.assertEqual(saida.name, "Relatório_csv_2")
        self.assertEqual((anterior / "frota.csv").read_text(), "anterior")

    def test_pbix_invalido_tem_mensagem_clara(self):
        with self.assertRaisesRegex(ValueError, r"arquivo \.pbix válido"):
            exportacao.abrir_modelo(self.arquivo)


if __name__ == "__main__":
    unittest.main()

