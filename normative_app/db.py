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
    revisione: str
    data_pubblicazione: str
    data_entrata_vigore: str
    data_ultimo_aggiornamento: str
    categoria: str
    tag: str
    percorso: str
    dimensione_su_disco: int
    monitorata: int
    disponibile: int
    disponibilita_minima: str
    stato: str
    raccolta: str
    profilo_qualita: str
    fonte: str
    note: str


EXPECTED_COLUMNS: dict[str, str] = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "titolo": "TEXT NOT NULL DEFAULT ''",
    "ente": "TEXT NOT NULL DEFAULT ''",
    "codice": "TEXT NOT NULL DEFAULT ''",
    "revisione": "TEXT NOT NULL DEFAULT ''",
    "data_pubblicazione": "TEXT NOT NULL DEFAULT ''",
    "data_entrata_vigore": "TEXT NOT NULL DEFAULT ''",
    "data_ultimo_aggiornamento": "TEXT NOT NULL DEFAULT ''",
    "categoria": "TEXT NOT NULL DEFAULT ''",
    "tag": "TEXT NOT NULL DEFAULT ''",
    "percorso": "TEXT NOT NULL DEFAULT ''",
    "dimensione_su_disco": "INTEGER NOT NULL DEFAULT 0",
    "monitorata": "INTEGER NOT NULL DEFAULT 1",
    "disponibile": "INTEGER NOT NULL DEFAULT 0",
    "disponibilita_minima": "TEXT NOT NULL DEFAULT ''",
    "stato": "TEXT NOT NULL DEFAULT ''",
    "raccolta": "TEXT NOT NULL DEFAULT ''",
    "profilo_qualita": "TEXT NOT NULL DEFAULT ''",
    "fonte": "TEXT NOT NULL DEFAULT ''",
    "note": "TEXT NOT NULL DEFAULT ''",
    "created_at": "TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
}


def get_connection(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection(db_path) as connection:
        columns = ",\n                ".join(
            f"{name} {definition}" for name, definition in EXPECTED_COLUMNS.items()
        )
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS normative (
                {columns}
            )
            """
        )
        _ensure_columns(connection)
        connection.commit()


def _ensure_columns(connection: sqlite3.Connection) -> None:
    existing = {
        row["name"] for row in connection.execute("PRAGMA table_info(normative)").fetchall()
    }
    for name, definition in EXPECTED_COLUMNS.items():
        if name in existing:
            continue
        connection.execute(f"ALTER TABLE normative ADD COLUMN {name} {definition}")


def insert_normativa(db_path: Path, normativa: Normativa) -> None:
    with get_connection(db_path) as connection:
        connection.execute(
            """
            INSERT INTO normative (
                titolo,
                ente,
                codice,
                revisione,
                data_pubblicazione,
                data_entrata_vigore,
                data_ultimo_aggiornamento,
                categoria,
                tag,
                percorso,
                dimensione_su_disco,
                monitorata,
                disponibile,
                disponibilita_minima,
                stato,
                raccolta,
                profilo_qualita,
                fonte,
                note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                normativa.titolo,
                normativa.ente,
                normativa.codice,
                normativa.revisione,
                normativa.data_pubblicazione,
                normativa.data_entrata_vigore,
                normativa.data_ultimo_aggiornamento,
                normativa.categoria,
                normativa.tag,
                normativa.percorso,
                normativa.dimensione_su_disco,
                normativa.monitorata,
                normativa.disponibile,
                normativa.disponibilita_minima,
                normativa.stato,
                normativa.raccolta,
                normativa.profilo_qualita,
                normativa.fonte,
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
                   revisione,
                   data_pubblicazione,
                   data_entrata_vigore,
                   data_ultimo_aggiornamento,
                   categoria,
                   tag,
                   percorso,
                   dimensione_su_disco,
                   monitorata,
                   disponibile,
                   disponibilita_minima,
                   stato,
                   raccolta,
                   profilo_qualita,
                   fonte,
                   note,
                   created_at
            FROM normative
            ORDER BY datetime(created_at) DESC
            """
        ).fetchall()
