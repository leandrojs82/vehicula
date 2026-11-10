"""Estruturas compartilhadas. Não importam interface nem arquivos de entrada."""
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime


@dataclass
class Row:
    number: int
    values: dict


@dataclass
class Issue:
    row: int
    column: str
    value: str
    reason: str
    blocking: bool = False
    source: str = ''


@dataclass
class Table:
    source: Path
    sheet: str
    headers: tuple
    rows: list
    issues: list = field(default_factory=list)
    date_epoch: datetime = datetime(1899, 12, 30)


@dataclass
class Candidate:
    situation: str
    query: str
    lines: list = field(default_factory=list)
    issues: list = field(default_factory=list)


@dataclass
class Reference:
    label: str
    index: dict
    issues: list = field(default_factory=list)


@dataclass
class Match:
    status: str
    candidates: list
    needs_review: bool
    manual: bool = False
    source_label: str = ''


@dataclass
class Change:
    row: int
    column: str
    before: str
    after: str


@dataclass
class Confirmation:
    row: int
    column: str
    value: str
    reason: str


@dataclass
class Session:
    source: Path
    sheet: str
    flow: str
    rows: list
    issues: list
    original_movements: dict
    reference: Reference | None = None
    matches: dict = field(default_factory=dict)
    overrides: dict = field(default_factory=dict)
    changes: list = field(default_factory=list)
    date_epoch: datetime = datetime(1899, 12, 30)
    confirmations: dict = field(default_factory=dict)
    supplemental_references: list = field(default_factory=list)

    def row(self, number):
        for row in self.rows:
            if row.number == number:
                return row
        from .errors import AppError
        raise AppError('Linha não encontrada: ' + str(number))


@dataclass
class ExportResult:
    csv: Path
    report: Path
    rows: int
