from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class Normativa:
    titolo: str
    ente: str
    codice: str
    versione: str
    data_pubblicazione: str
    categoria: str
    tag: str
    path_file_locale: str
    stato: str
    note: str


def get_connection(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS normative (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titolo TEXT NOT NULL,
                ente TEXT NOT NULL,
                codice TEXT NOT NULL,
                versione TEXT NOT NULL,
                data_pubblicazione TEXT NOT NULL,
                categoria TEXT NOT NULL,
                tag TEXT NOT NULL,
                path_file_locale TEXT NOT NULL,
                stato TEXT NOT NULL,
                note TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def insert_normativa(db_path: Path, normativa: Normativa) -> None:
    with get_connection(db_path) as connection:
        connection.execute(
            """
            INSERT INTO normative (
                titolo,
                ente,
                codice,
                versione,
                data_pubblicazione,
                categoria,
                tag,
                path_file_locale,
                stato,
                note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                normativa.titolo,
                normativa.ente,
                normativa.codice,
                normativa.versione,
                normativa.data_pubblicazione,
                normativa.categoria,
                normativa.tag,
                normativa.path_file_locale,
                normativa.stato,
                normativa.note,
            ),
        )
        connection.commit()


def list_normative(db_path: Path) -> Iterable[sqlite3.Row]:
    with get_connection(db_path) as connection:
        return connection.execute(
            """
            SELECT id,
                   titolo,
                   ente,
                   codice,
                   versione,
                   data_pubblicazione,
                   categoria,
                   tag,
                   path_file_locale,
                   stato,
                   note,
                   created_at
            FROM normative
            ORDER BY datetime(created_at) DESC
            """
        ).fetchall()
