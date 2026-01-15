from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from normative_app.db import Normativa, init_db, insert_normativa, list_normative


CATEGORIES = [
    "Urbanistica",
    "Edilizia",
    "Sicurezza",
    "Ambiente",
    "Energia",
    "Impianti",
    "Antincendio",
    "Accessibilità",
    "Lavoro",
    "Privacy",
    "Trasporti",
    "Sanità",
    "Altre",
]

STATES = ["attiva", "superata"]


def get_app_data_dir() -> Path:
    if sys.platform.startswith("win"):
        base_dir = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base_dir = Path.home() / "Library" / "Application Support"
    else:
        base_dir = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base_dir / "NormativeCatalogo"


def open_path(path: str) -> None:
    if not path:
        return
    path_obj = Path(path)
    if not path_obj.exists():
        QtWidgets.QMessageBox.warning(
            None,
            "File non trovato",
            f"Il file non esiste: {path}",
        )
        return
    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        os.system(f"open '{path}'")
    else:
        os.system(f"xdg-open '{path}'")


class NormativaForm(QtWidgets.QWidget):
    submitted = QtCore.Signal()

    def __init__(self) -> None:
        super().__init__()
        self.titolo_input = QtWidgets.QLineEdit()
        self.ente_input = QtWidgets.QLineEdit()
        self.codice_input = QtWidgets.QLineEdit()
        self.versione_input = QtWidgets.QLineEdit()
        self.data_pubblicazione_input = QtWidgets.QDateEdit()
        self.data_pubblicazione_input.setCalendarPopup(True)
        self.data_pubblicazione_input.setDate(QtCore.QDate.currentDate())
        self.categoria_input = QtWidgets.QComboBox()
        self.categoria_input.addItems(CATEGORIES)
        self.tag_input = QtWidgets.QLineEdit()
        self.path_file_input = QtWidgets.QLineEdit()
        self.path_file_button = QtWidgets.QPushButton("Sfoglia")
        self.stato_input = QtWidgets.QComboBox()
        self.stato_input.addItems(STATES)
        self.note_input = QtWidgets.QPlainTextEdit()
        self.submit_button = QtWidgets.QPushButton("Salva normativa")
        self._build_layout()
        self.path_file_button.clicked.connect(self._select_file)
        self.submit_button.clicked.connect(self._handle_submit)

    def _build_layout(self) -> None:
        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow("Titolo", self.titolo_input)
        form_layout.addRow("Ente", self.ente_input)
        form_layout.addRow("Codice", self.codice_input)
        form_layout.addRow("Versione", self.versione_input)
        form_layout.addRow("Data pubblicazione", self.data_pubblicazione_input)
        form_layout.addRow("Categoria", self.categoria_input)
        form_layout.addRow("Tag (separati da virgola)", self.tag_input)

        file_layout = QtWidgets.QHBoxLayout()
        file_layout.addWidget(self.path_file_input)
        file_layout.addWidget(self.path_file_button)
        form_layout.addRow("File locale", file_layout)

        form_layout.addRow("Stato", self.stato_input)
        form_layout.addRow("Note", self.note_input)

        container = QtWidgets.QVBoxLayout(self)
        container.addLayout(form_layout)
        container.addWidget(self.submit_button)

    def _select_file(self) -> None:
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Seleziona file")
        if file_path:
            self.path_file_input.setText(file_path)

    def _handle_submit(self) -> None:
        if not self.titolo_input.text().strip():
            QtWidgets.QMessageBox.warning(self, "Campo obbligatorio", "Inserisci il titolo.")
            return
        if not self.codice_input.text().strip():
            QtWidgets.QMessageBox.warning(self, "Campo obbligatorio", "Inserisci il codice.")
            return
        self.submitted.emit()

    def to_normativa(self) -> Normativa:
        return Normativa(
            titolo=self.titolo_input.text().strip(),
            ente=self.ente_input.text().strip(),
            codice=self.codice_input.text().strip(),
            versione=self.versione_input.text().strip(),
            data_pubblicazione=self.data_pubblicazione_input.date().toString("yyyy-MM-dd"),
            categoria=self.categoria_input.currentText(),
            tag=self.tag_input.text().strip(),
            path_file_locale=self.path_file_input.text().strip(),
            stato=self.stato_input.currentText(),
            note=self.note_input.toPlainText().strip(),
        )

    def reset(self) -> None:
        self.titolo_input.clear()
        self.ente_input.clear()
        self.codice_input.clear()
        self.versione_input.clear()
        self.data_pubblicazione_input.setDate(QtCore.QDate.currentDate())
        self.categoria_input.setCurrentIndex(0)
        self.tag_input.clear()
        self.path_file_input.clear()
        self.stato_input.setCurrentIndex(0)
        self.note_input.clear()


class NormativaTable(QtWidgets.QTableWidget):
    def __init__(self) -> None:
        super().__init__(0, 9)
        self.setHorizontalHeaderLabels(
            [
                "Titolo",
                "Ente",
                "Codice",
                "Versione",
                "Data",
                "Categoria",
                "Tag",
                "Stato",
                "File locale",
            ]
        )
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

    def load(self, rows: list[QtCore.QVariant]) -> None:
        self.setRowCount(0)
        for row in rows:
            row_position = self.rowCount()
            self.insertRow(row_position)
            values = [
                row["titolo"],
                row["ente"],
                row["codice"],
                row["versione"],
                row["data_pubblicazione"],
                row["categoria"],
                row["tag"],
                row["stato"],
                row["path_file_locale"],
            ]
            for col, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(str(value))
                if col == 8:
                    item.setToolTip(str(value))
                self.setItem(row_position, col, item)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, db_path: Path) -> None:
        super().__init__()
        self.db_path = db_path
        self.setWindowTitle("Catalogo Normative")
        self.resize(1100, 700)

        self.form = NormativaForm()
        self.table = NormativaTable()
        self.refresh_button = QtWidgets.QPushButton("Aggiorna elenco")
        self.export_button = QtWidgets.QPushButton("Export bibliografia (.txt)")
        self.open_file_button = QtWidgets.QPushButton("Apri file selezionato")

        self._build_layout()
        self._connect_signals()
        self.refresh_table()

    def _build_layout(self) -> None:
        content = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(content)

        actions_layout = QtWidgets.QHBoxLayout()
        actions_layout.addWidget(self.refresh_button)
        actions_layout.addWidget(self.export_button)
        actions_layout.addWidget(self.open_file_button)
        actions_layout.addStretch()

        layout.addLayout(actions_layout)
        layout.addWidget(self.table)
        layout.addWidget(self.form)
        self.setCentralWidget(content)

    def _connect_signals(self) -> None:
        self.form.submitted.connect(self._save_normativa)
        self.refresh_button.clicked.connect(self.refresh_table)
        self.export_button.clicked.connect(self.export_txt)
        self.open_file_button.clicked.connect(self.open_selected_file)

    def _save_normativa(self) -> None:
        normativa = self.form.to_normativa()
        insert_normativa(self.db_path, normativa)
        self.form.reset()
        self.refresh_table()

    def refresh_table(self) -> None:
        rows = list(list_normative(self.db_path))
        self.table.load(rows)

    def export_txt(self) -> None:
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Salva bibliografia",
            "bibliografia_normative.txt",
            "File di testo (*.txt)",
        )
        if not file_path:
            return
        rows = list(list_normative(self.db_path))
        with open(file_path, "w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(
                    f"{row['titolo']} ({row['codice']}), {row['ente']}, "
                    f"{row['versione']} - {row['data_pubblicazione']}\n"
                )
        QtWidgets.QMessageBox.information(
            self,
            "Export completato",
            f"File salvato in: {file_path}",
        )

    def open_selected_file(self) -> None:
        selected = self.table.selectedItems()
        if not selected:
            QtWidgets.QMessageBox.information(
                self,
                "Seleziona una riga",
                "Seleziona una normativa per aprire il file.",
            )
            return
        row = selected[0].row()
        path_item = self.table.item(row, 8)
        if not path_item:
            return
        open_path(path_item.text())


class NormativaApp(QtWidgets.QApplication):
    def __init__(self, db_path: Path) -> None:
        super().__init__(sys.argv)
        self.db_path = db_path

    def run(self) -> int:
        window = MainWindow(self.db_path)
        window.show()
        return self.exec()


def run() -> int:
    db_path = get_app_data_dir() / "normative.db"
    init_db(db_path)
    app = NormativaApp(db_path)
    return app.run()
