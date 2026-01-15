from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PublicSource:
    nome: str
    ente: str
    url: str
    copertura: str
    paese: str
    licenza: str
    note: str


PUBLIC_SOURCES: tuple[PublicSource, ...] = (
    PublicSource(
        nome="ISO Catalogue",
        ente="International Organization for Standardization (ISO)",
        url="https://www.iso.org/standards.html",
        copertura="Standard internazionali multi-settore",
        paese="Internazionale",
        licenza="Metadati consultabili; testi completi a pagamento",
        note="Catalogo ufficiale ISO per ricerca e metadata.",
    ),
    PublicSource(
        nome="IEC Webstore",
        ente="International Electrotechnical Commission (IEC)",
        url="https://webstore.iec.ch/",
        copertura="Elettrotecnica ed elettronica",
        paese="Internazionale",
        licenza="Metadati pubblici; documenti completi con licenza",
        note="Catalogo IEC con dati di pubblicazione.",
    ),
    PublicSource(
        nome="IEEE Standards",
        ente="Institute of Electrical and Electronics Engineers (IEEE)",
        url="https://standards.ieee.org/standard/",
        copertura="Elettrotecnica, telecomunicazioni, informatica",
        paese="Internazionale",
        licenza="Metadati pubblici; testi completi con licenza",
        note="Portale di ricerca norme IEEE.",
    ),
    PublicSource(
        nome="ASTM Standards",
        ente="ASTM International",
        url="https://www.astm.org/standards.html",
        copertura="Materiali, prove, processi industriali",
        paese="Internazionale",
        licenza="Metadati pubblici; testi completi a pagamento",
        note="Catalogo ASTM per standard tecnici.",
    ),
    PublicSource(
        nome="ASME Standards",
        ente="American Society of Mechanical Engineers (ASME)",
        url="https://www.asme.org/codes-standards",
        copertura="Ingegneria meccanica, pressure vessels",
        paese="USA",
        licenza="Metadati pubblici; accesso a pagamento",
        note="Codici e standard ASME.",
    ),
    PublicSource(
        nome="API Standards",
        ente="American Petroleum Institute (API)",
        url="https://www.api.org/products-and-services/standards",
        copertura="Oil & Gas, sicurezza impianti",
        paese="USA",
        licenza="Metadati pubblici; accesso con licenza",
        note="Standard tecnici per industria energetica.",
    ),
    PublicSource(
        nome="SAE Mobilus",
        ente="SAE International",
        url="https://www.sae.org/standards",
        copertura="Automotive, aerospace, mobilità",
        paese="USA",
        licenza="Metadati pubblici; accesso con licenza",
        note="Catalogo standard SAE.",
    ),
    PublicSource(
        nome="ACI Codes",
        ente="American Concrete Institute (ACI)",
        url="https://www.concrete.org/store/productsearch.aspx",
        copertura="Calcestruzzo, strutture",
        paese="USA",
        licenza="Metadati pubblici; testi con licenza",
        note="Catalogo codici e standard ACI.",
    ),
    PublicSource(
        nome="AISC Standards",
        ente="American Institute of Steel Construction (AISC)",
        url="https://www.aisc.org/publications/standards/",
        copertura="Strutture in acciaio",
        paese="USA",
        licenza="Metadati pubblici; alcuni documenti open access",
        note="Standard e specifiche acciaio strutturale.",
    ),
    PublicSource(
        nome="NFPA Codes & Standards",
        ente="National Fire Protection Association (NFPA)",
        url="https://www.nfpa.org/codes-and-standards",
        copertura="Sicurezza antincendio",
        paese="USA",
        licenza="Metadati pubblici; testi consultabili con licenze NFPA",
        note="Catalogo codici antincendio.",
    ),
    PublicSource(
        nome="CEN Standards",
        ente="European Committee for Standardization (CEN)",
        url="https://standards.cencenelec.eu/",
        copertura="Standard europei multi-settore",
        paese="Europa",
        licenza="Metadati consultabili; testi completi tramite enti nazionali",
        note="Ricerca standard europei EN.",
    ),
    PublicSource(
        nome="CENELEC Standards",
        ente="European Committee for Electrotechnical Standardization (CENELEC)",
        url="https://standards.cencenelec.eu/",
        copertura="Elettrotecnica europea",
        paese="Europa",
        licenza="Metadati consultabili; testi completi tramite enti nazionali",
        note="Standard EN per elettrotecnica.",
    ),
    PublicSource(
        nome="ETSI Standards",
        ente="European Telecommunications Standards Institute (ETSI)",
        url="https://www.etsi.org/standards",
        copertura="Telecomunicazioni e ICT",
        paese="Europa",
        licenza="Metadati e documenti spesso open access",
        note="Catalogo standard ETSI con accesso pubblico.",
    ),
    PublicSource(
        nome="UNI Standards",
        ente="Ente Italiano di Normazione (UNI)",
        url="https://store.uni.com/",
        copertura="Norme tecniche italiane multi-settore",
        paese="Italia",
        licenza="Metadati pubblici; testi completi con licenza",
        note="Catalogo UNI ufficiale.",
    ),
    PublicSource(
        nome="CEI Standards",
        ente="Comitato Elettrotecnico Italiano (CEI)",
        url="https://mycatalogo.ceinorme.it/",
        copertura="Elettrotecnica italiana",
        paese="Italia",
        licenza="Metadati pubblici; testi completi con licenza",
        note="Catalogo CEI per norme elettrotecniche.",
    ),
    PublicSource(
        nome="DIN Standards",
        ente="Deutsches Institut für Normung (DIN)",
        url="https://www.din.de/en/services/din-spec-en",
        copertura="Norme tecniche tedesche",
        paese="Germania",
        licenza="Metadati pubblici; testi completi con licenza",
        note="Portale DIN per norme e specifiche.",
    ),
    PublicSource(
        nome="BSI Standards",
        ente="British Standards Institution (BSI)",
        url="https://www.bsigroup.com/en-GB/standards/",
        copertura="Norme tecniche britanniche",
        paese="Regno Unito",
        licenza="Metadati pubblici; testi completi con licenza",
        note="Catalogo norme BSI.",
    ),
    PublicSource(
        nome="EUR-Lex",
        ente="Unione Europea",
        url="https://eur-lex.europa.eu/",
        copertura="Normativa e regolamenti UE",
        paese="Europa",
        licenza="Riutilizzo dati UE con attribuzione",
        note="Portale ufficiale legislativo UE.",
    ),
    PublicSource(
        nome="Gazzetta Ufficiale Italiana",
        ente="Istituto Poligrafico e Zecca dello Stato",
        url="https://www.gazzettaufficiale.it/",
        copertura="Normativa nazionale italiana",
        paese="Italia",
        licenza="Verificare termini di riuso",
        note="Accesso a metadati di pubblicazione nazionale.",
    ),
    PublicSource(
        nome="NIST Standards",
        ente="National Institute of Standards and Technology (NIST)",
        url="https://www.nist.gov/standardsgov",
        copertura="Standard e linee guida tecniche",
        paese="USA",
        licenza="Documenti spesso open access",
        note="Repository federale per standard e linee guida.",
    ),
    PublicSource(
        nome="IETF RFC",
        ente="Internet Engineering Task Force (IETF)",
        url="https://www.rfc-editor.org/",
        copertura="Standard Internet e protocolli",
        paese="Internazionale",
        licenza="Open access",
        note="RFC Editor per standard tecnici di rete.",
    ),
    PublicSource(
        nome="W3C Recommendations",
        ente="World Wide Web Consortium (W3C)",
        url="https://www.w3.org/TR/",
        copertura="Standard web e accessibilità",
        paese="Internazionale",
        licenza="Open access",
        note="Raccomandazioni tecniche W3C.",
    ),
)


def get_centralized_db_path() -> Path:
    if os.name == "nt":
        base_dir = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif os.uname().sysname.lower() == "darwin":
        base_dir = Path.home() / "Library" / "Application Support"
    else:
        base_dir = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base_dir / "NormativeCatalogo" / "centralized_normative.db"


def get_connection(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_centralized_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS fonti_pubbliche (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                ente TEXT NOT NULL,
                url TEXT NOT NULL,
                copertura TEXT NOT NULL DEFAULT '',
                paese TEXT NOT NULL DEFAULT '',
                licenza TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS norme_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titolo TEXT NOT NULL,
                ente TEXT NOT NULL,
                codice TEXT NOT NULL,
                categoria TEXT NOT NULL DEFAULT '',
                paese TEXT NOT NULL DEFAULT '',
                data_pubblicazione TEXT NOT NULL DEFAULT '',
                data_ultimo_aggiornamento TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                fonte_id INTEGER,
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (fonte_id) REFERENCES fonti_pubbliche(id)
            )
            """
        )
        _seed_public_sources(connection)
        connection.commit()


def _seed_public_sources(connection: sqlite3.Connection) -> None:
    existing = connection.execute("SELECT COUNT(1) AS total FROM fonti_pubbliche").fetchone()
    if existing and existing["total"] > 0:
        return
    connection.executemany(
        """
        INSERT INTO fonti_pubbliche (
            nome,
            ente,
            url,
            copertura,
            paese,
            licenza,
            note
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                source.nome,
                source.ente,
                source.url,
                source.copertura,
                source.paese,
                source.licenza,
                source.note,
            )
            for source in PUBLIC_SOURCES
        ],
    )


def main() -> int:
    db_path = get_centralized_db_path()
    init_centralized_db(db_path)
    print(f"Database centralizzato creato in: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
