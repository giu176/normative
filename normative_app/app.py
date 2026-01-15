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

AVAILABILITY_MINIMUM = ["Annunciata", "In consultazione", "Pubblicata"]
STATES = ["In bozza", "Annunciata", "In consultazione", "Pubblicata", "Abrogata"]


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
        self.revisione_input = QtWidgets.QLineEdit()
        self.data_pubblicazione_input = QtWidgets.QDateEdit()
        self.data_pubblicazione_input.setCalendarPopup(True)
        self.data_pubblicazione_input.setDate(QtCore.QDate.currentDate())
        self.data_entrata_vigore_input = QtWidgets.QDateEdit()
        self.data_entrata_vigore_input.setCalendarPopup(True)
        self.data_entrata_vigore_input.setDate(QtCore.QDate.currentDate())
        self.data_ultimo_aggiornamento_input = QtWidgets.QDateEdit()
        self.data_ultimo_aggiornamento_input.setCalendarPopup(True)
        self.data_ultimo_aggiornamento_input.setDate(QtCore.QDate.currentDate())
        self.categoria_input = QtWidgets.QComboBox()
        self.categoria_input.addItems(CATEGORIES)
        self.tag_input = QtWidgets.QLineEdit()
        self.path_file_input = QtWidgets.QLineEdit()
        self.path_file_button = QtWidgets.QPushButton("Sfoglia")
        self.dimensione_input = QtWidgets.QSpinBox()
        self.dimensione_input.setRange(0, 10_000_000)
        self.dimensione_input.setSuffix(" KB")
        self.monitorata_input = QtWidgets.QCheckBox("Monitorata")
        self.monitorata_input.setChecked(True)
        self.disponibile_input = QtWidgets.QCheckBox("Disponibile")
        self.disponibilita_minima_input = QtWidgets.QComboBox()
        self.disponibilita_minima_input.addItems(AVAILABILITY_MINIMUM)
        self.stato_input = QtWidgets.QComboBox()
        self.stato_input.addItems(STATES)
        self.raccolta_input = QtWidgets.QLineEdit()
        self.profilo_qualita_input = QtWidgets.QLineEdit()
        self.fonte_input = QtWidgets.QLineEdit()
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
        form_layout.addRow("Revisione", self.revisione_input)
        form_layout.addRow("Data pubblicazione", self.data_pubblicazione_input)
        form_layout.addRow("Data entrata in vigore", self.data_entrata_vigore_input)
        form_layout.addRow("Data ultimo aggiornamento", self.data_ultimo_aggiornamento_input)
        form_layout.addRow("Categoria", self.categoria_input)
        form_layout.addRow("Tag (separati da virgola)", self.tag_input)

        file_layout = QtWidgets.QHBoxLayout()
        file_layout.addWidget(self.path_file_input)
        file_layout.addWidget(self.path_file_button)
        form_layout.addRow("Percorso file", file_layout)

        form_layout.addRow("Dimensione su disco", self.dimensione_input)
        form_layout.addRow(self.monitorata_input, self.disponibile_input)
        form_layout.addRow("Disponibilità minima", self.disponibilita_minima_input)
        form_layout.addRow("Stato", self.stato_input)
        form_layout.addRow("Raccolta", self.raccolta_input)
        form_layout.addRow("Profilo qualità", self.profilo_qualita_input)
        form_layout.addRow("Fonte", self.fonte_input)
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
            revisione=self.revisione_input.text().strip(),
            data_pubblicazione=self.data_pubblicazione_input.date().toString("yyyy-MM-dd"),
            data_entrata_vigore=self.data_entrata_vigore_input.date().toString("yyyy-MM-dd"),
            data_ultimo_aggiornamento=self.data_ultimo_aggiornamento_input.date().toString(
                "yyyy-MM-dd"
            ),
            categoria=self.categoria_input.currentText(),
            tag=self.tag_input.text().strip(),
            percorso=self.path_file_input.text().strip(),
            dimensione_su_disco=self.dimensione_input.value(),
            monitorata=1 if self.monitorata_input.isChecked() else 0,
            disponibile=1 if self.disponibile_input.isChecked() else 0,
            disponibilita_minima=self.disponibilita_minima_input.currentText(),
            stato=self.stato_input.currentText(),
            raccolta=self.raccolta_input.text().strip(),
            profilo_qualita=self.profilo_qualita_input.text().strip(),
            fonte=self.fonte_input.text().strip(),
            note=self.note_input.toPlainText().strip(),
        )

    def reset(self) -> None:
        self.titolo_input.clear()
        self.ente_input.clear()
        self.codice_input.clear()
        self.revisione_input.clear()
        self.data_pubblicazione_input.setDate(QtCore.QDate.currentDate())
        self.data_entrata_vigore_input.setDate(QtCore.QDate.currentDate())
        self.data_ultimo_aggiornamento_input.setDate(QtCore.QDate.currentDate())
        self.categoria_input.setCurrentIndex(0)
        self.tag_input.clear()
        self.path_file_input.clear()
        self.dimensione_input.setValue(0)
        self.monitorata_input.setChecked(True)
        self.disponibile_input.setChecked(False)
        self.disponibilita_minima_input.setCurrentIndex(0)
        self.stato_input.setCurrentIndex(0)
        self.raccolta_input.clear()
        self.profilo_qualita_input.clear()
        self.fonte_input.clear()
        self.note_input.clear()


class NormativaTable(QtWidgets.QTableWidget):
    def __init__(self) -> None:
        super().__init__(0, 11)
        self.setHorizontalHeaderLabels(
            [
                "Titolo",
                "Ente",
                "Codice",
                "Revisione",
                "Pubblicazione",
                "Categoria",
                "Tag",
                "Monitorata",
                "Disponibile",
                "Stato",
                "Percorso file",
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
                row["revisione"],
                row["data_pubblicazione"],
                row["categoria"],
                row["tag"],
                "Sì" if row["monitorata"] else "No",
                "Sì" if row["disponibile"] else "No",
                row["stato"],
                row["percorso"],
            ]
            for col, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(str(value))
                if col == 10:
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
        self.clear_filters_button = QtWidgets.QPushButton("Pulisci filtri")

        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Titolo, codice o ente")
        self.category_filter = QtWidgets.QComboBox()
        self.category_filter.addItems(["Tutte"] + CATEGORIES)
        self.status_filter = QtWidgets.QComboBox()
        self.status_filter.addItems(["Tutti"] + STATES)
        self.monitor_filter = QtWidgets.QComboBox()
        self.monitor_filter.addItems(["Tutte", "Monitorate", "Non monitorate"])
        self.availability_filter = QtWidgets.QComboBox()
        self.availability_filter.addItems(["Tutte", "Disponibili", "Mancanti"])
        self.availability_min_filter = QtWidgets.QComboBox()
        self.availability_min_filter.addItems(["Tutte"] + AVAILABILITY_MINIMUM)
        self.tag_filter = QtWidgets.QLineEdit()
        self.tag_filter.setPlaceholderText("Es. sicurezza, urbano")

        self.results_label = QtWidgets.QLabel()
        self.tabs = QtWidgets.QTabWidget()
        self.catalog_page = QtWidgets.QWidget()
        self.form_page = QtWidgets.QWidget()
        self.all_rows: list[QtCore.QVariant] = []

        self._build_layout()
        self._connect_signals()
        self.refresh_table()

    def _build_layout(self) -> None:
        self._build_catalog_layout()
        self._build_form_layout()

        self.tabs.addTab(self.catalog_page, "Catalogo")
        self.tabs.addTab(self.form_page, "Inserimento manuale")
        self.setCentralWidget(self.tabs)

    def _build_catalog_layout(self) -> None:
        layout = QtWidgets.QVBoxLayout(self.catalog_page)

        filters_group = QtWidgets.QGroupBox("Filtri")
        filters_layout = QtWidgets.QGridLayout(filters_group)
        filters_layout.addWidget(QtWidgets.QLabel("Ricerca"), 0, 0)
        filters_layout.addWidget(self.search_input, 0, 1)
        filters_layout.addWidget(QtWidgets.QLabel("Categoria"), 0, 2)
        filters_layout.addWidget(self.category_filter, 0, 3)
        filters_layout.addWidget(QtWidgets.QLabel("Stato"), 1, 0)
        filters_layout.addWidget(self.status_filter, 1, 1)
        filters_layout.addWidget(QtWidgets.QLabel("Monitoraggio"), 1, 2)
        filters_layout.addWidget(self.monitor_filter, 1, 3)
        filters_layout.addWidget(QtWidgets.QLabel("Disponibilità"), 2, 0)
        filters_layout.addWidget(self.availability_filter, 2, 1)
        filters_layout.addWidget(QtWidgets.QLabel("Disponibilità minima"), 2, 2)
        filters_layout.addWidget(self.availability_min_filter, 2, 3)
        filters_layout.addWidget(QtWidgets.QLabel("Tag"), 3, 0)
        filters_layout.addWidget(self.tag_filter, 3, 1, 1, 3)
        filters_layout.addWidget(self.clear_filters_button, 0, 4, 2, 1)
        filters_layout.setColumnStretch(1, 2)
        filters_layout.setColumnStretch(3, 2)

        actions_layout = QtWidgets.QHBoxLayout()
        actions_layout.addWidget(self.refresh_button)
        actions_layout.addWidget(self.export_button)
        actions_layout.addWidget(self.open_file_button)
        actions_layout.addStretch()
        actions_layout.addWidget(self.results_label)

        layout.addWidget(filters_group)
        layout.addLayout(actions_layout)
        layout.addWidget(self.table)

    def _build_form_layout(self) -> None:
        layout = QtWidgets.QVBoxLayout(self.form_page)
        title = QtWidgets.QLabel("Inserisci una normativa manualmente")
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        layout.addWidget(title)
        layout.addWidget(self.form)
        layout.addStretch()

    def _connect_signals(self) -> None:
        self.form.submitted.connect(self._save_normativa)
        self.refresh_button.clicked.connect(self.refresh_table)
        self.export_button.clicked.connect(self.export_txt)
        self.open_file_button.clicked.connect(self.open_selected_file)
        self.clear_filters_button.clicked.connect(self.clear_filters)
        self.search_input.textChanged.connect(self.apply_filters)
        self.category_filter.currentIndexChanged.connect(self.apply_filters)
        self.status_filter.currentIndexChanged.connect(self.apply_filters)
        self.monitor_filter.currentIndexChanged.connect(self.apply_filters)
        self.availability_filter.currentIndexChanged.connect(self.apply_filters)
        self.availability_min_filter.currentIndexChanged.connect(self.apply_filters)
        self.tag_filter.textChanged.connect(self.apply_filters)

    def _save_normativa(self) -> None:
        normativa = self.form.to_normativa()
        insert_normativa(self.db_path, normativa)
        self.form.reset()
        self.refresh_table()
        self.tabs.setCurrentWidget(self.catalog_page)

    def refresh_table(self) -> None:
        self.all_rows = list(list_normative(self.db_path))
        self.apply_filters()

    def apply_filters(self) -> None:
        search_text = self.search_input.text().strip().lower()
        tag_text = self.tag_filter.text().strip().lower()
        category = self.category_filter.currentText()
        status = self.status_filter.currentText()
        monitor_filter = self.monitor_filter.currentText()
        availability_filter = self.availability_filter.currentText()
        availability_min = self.availability_min_filter.currentText()

        filtered = []
        for row in self.all_rows:
            if category != "Tutte" and row["categoria"] != category:
                continue
            if status != "Tutti" and row["stato"] != status:
                continue
            if monitor_filter == "Monitorate" and not row["monitorata"]:
                continue
            if monitor_filter == "Non monitorate" and row["monitorata"]:
                continue
            if availability_filter == "Disponibili" and not row["disponibile"]:
                continue
            if availability_filter == "Mancanti" and row["disponibile"]:
                continue
            if availability_min != "Tutte" and row["disponibilita_minima"] != availability_min:
                continue
            if search_text:
                combined = f"{row['titolo']} {row['codice']} {row['ente']}".lower()
                if search_text not in combined:
                    continue
            if tag_text and tag_text not in row["tag"].lower():
                continue
            filtered.append(row)

        self.table.load(filtered)
        self.results_label.setText(f"Risultati: {len(filtered)}")

    def clear_filters(self) -> None:
        self.search_input.clear()
        self.tag_filter.clear()
        self.category_filter.setCurrentIndex(0)
        self.status_filter.setCurrentIndex(0)
        self.monitor_filter.setCurrentIndex(0)
        self.availability_filter.setCurrentIndex(0)
        self.availability_min_filter.setCurrentIndex(0)
        self.apply_filters()

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
                    f"{row['revisione']} - {row['data_pubblicazione']}\n"
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
        path_item = self.table.item(row, 10)
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
