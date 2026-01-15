# Catalogo Normative (prima versione)

Prima versione desktop per catalogare normative in locale (offline-first) con SQLite e UI Qt.

## Funzionalità incluse
- Inserimento manuale di una normativa con campi principali.
- Archivio locale su SQLite.
- Elenco delle normative con apertura del file locale.
- Export della bibliografia in `.txt`.

## Requisiti
- Python 3.10+.
- Windows 10/11 (funziona anche su macOS/Linux per sviluppo).

## Avvio in sviluppo
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Il database viene creato nella cartella dati utente:
- **Windows**: `%APPDATA%\NormativeCatalogo\normative.db`
- **macOS**: `~/Library/Application Support/NormativeCatalogo/normative.db`
- **Linux**: `~/.local/share/NormativeCatalogo/normative.db`

## Deploy su Windows (build .exe singolo)
> Obiettivo: generare un unico eseguibile `.exe` con tutte le dipendenze incluse.

1. **Prepara l’ambiente**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. **Costruisci l’eseguibile**
   ```bash
   pyinstaller --onefile --windowed --name NormativeCatalogo main.py
   ```

3. **Output**
   - Trovi l’eseguibile in `dist\NormativeCatalogo.exe`.
   - Il DB verrà creato al primo avvio in `%APPDATA%\NormativeCatalogo\normative.db`.

4. **Distribuzione**
   - Copia solo `dist\NormativeCatalogo.exe` su altri PC Windows.
   - Nessuna installazione di Python richiesta.

## Note per la versione 1
Questa prima versione mantiene i tag come stringa separata da virgola e usa una singola tabella SQLite. Le prossime versioni potranno introdurre la normalizzazione dei tag e lo storico versioni come da blueprint.

## Database centralizzato (solo metadata)
Per creare il database centralizzato con le fonti pubbliche degli standard e normative ingegneristiche:

```bash
python -m normative_app.centralized_db
```

Il database viene salvato nella stessa cartella dati utente dell'applicazione con nome `centralized_normative.db`.
