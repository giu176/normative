# Blueprint

## Stack tecnologico (scelta motivata)
**Scelta:** Python + Qt (PySide6) + SQLite.

**Motivazione:**
- Distribuzione semplice in ambienti aziendali/offline con pacchetti standalone.
- UI desktop nativa e reattiva con componenti maturi per tabelle, filtri e form.
- SQLite è leggero, embedded e ideale per un catalogo locale con indicizzazione.
- Python facilita scripting per import batch, validazioni e sincronizzazioni.

## Obiettivi
- Catalogare le normative in modo strutturato e coerente.
- Consentire l'aggiornamento delle normative nel tempo, mantenendo traccia delle versioni.
- Favorire il reperimento rapido delle normative tramite filtri e ricerca.
- Garantire il funzionamento offline dell'applicazione e la consultazione dei file locali.
- Permettere l'export in formato .txt per la bibliografia e la condivisione.

## Modello dati: Normativa
Campi consigliati:
- **titolo**: denominazione ufficiale della normativa.
- **ente**: organismo/ente emanatore.
- **codice**: identificativo ufficiale o interno.
- **versione**: stringa di versione o numero di revisione.
- **data_pubblicazione**: data di pubblicazione ufficiale.
- **categoria**: categoria principale (vedi tassonomia).
- **tag**: elenco di parole chiave/etichette.
- **path_file_locale**: percorso del file locale associato.
- **stato**: `attiva` oppure `superata`.
- **note**: annotazioni libere.

## Tassonomia
### Categorie (elenco fornito)
- Urbanistica
- Edilizia
- Sicurezza
- Ambiente
- Energia
- Impianti
- Antincendio
- Accessibilità
- Lavoro
- Privacy
- Trasporti
- Sanità
- Altre

### Tag
Esempi di tag iniziali:
- `regionale`
- `nazionale`
- `europea`
- `linee-guida`
- `aggiornamento-urgente`

Sistema di estensione:
- Ogni normativa può avere più tag.
- I tag sono aggiungibili liberamente dagli utenti per estendere la classificazione.
- Il sistema suggerisce tag esistenti ma consente la creazione di nuovi.

## Flussi utente
- **Selezione filtri**: l'utente seleziona categoria, tag, stato o periodo per filtrare.
- **Elenco per categoria**: elenco delle normative raggruppate per categoria.
- **Download .txt**: export della bibliografia o di selezioni filtrate in .txt.
- **Consultazione file locali**: apertura del file locale dal path salvato.
- **Inserimento manuale/automatico**: creazione di record via form o import.
- **Modifica parametri**: aggiornamento di metadati, tag, stato o percorso file.

## Moduli principali
1. **Catalogo locale (DB)**
   - CRUD normative, categorie e tag.
   - Ricerca full-text e filtri avanzati (categoria, tag, stato, periodo).
   - Gestione versioni e storico.
2. **Gestione file**
   - Associazione file locali e apertura tramite OS.
   - Spostamento versioni superate in `/SUP`.
   - Verifica integrità path e presenza file.
3. **Filtri/Tag**
   - Gestione tassonomia: categorie predefinite e tag liberi.
   - Suggerimenti tag e conteggi per filtro rapido.
4. **Export .txt**
   - Esportazione bibliografia filtrata con formattazione standard.
5. **Ingestione**
   - Manuale: form con validazioni obbligatorie.
   - Batch: import CSV/Excel con mapping colonne e controlli.
6. **Update online**
   - Sincronizzazione metadati e confronto versioni.
   - Log aggiornamenti e notifiche.

## Database locale (SQLite)
**Tabelle principali:**
- **normative**
  - `id` (PK), `titolo`, `ente`, `codice`, `data_pubblicazione`,
    `categoria_id` (FK), `stato`, `note`, `created_at`, `updated_at`.
- **categorie**
  - `id` (PK), `nome`, `descrizione`.
- **tag**
  - `id` (PK), `nome` (unique).
- **normativa_tag**
  - `normativa_id` (FK), `tag_id` (FK), PK composta.
- **versioni**
  - `id` (PK), `normativa_id` (FK), `versione`,
    `data_pubblicazione`, `file_path_id` (FK), `is_corrente`.
- **file_path**
  - `id` (PK), `path_assoluto`, `hash`, `dimensione`, `created_at`.

**Indici suggeriti:**
- `normative(categoria_id, stato)`
- `tag(nome)`
- `versioni(normativa_id, is_corrente)`
- `file_path(path_assoluto)`

## Flusso offline (locale)
1. **Caricamento locale**: l'utente seleziona file o importa batch.
2. **Validazione**: controlli su campi obbligatori e formato date.
3. **Tagging**: assegnazione tag e categoria.
4. **Ricerca/filtri**: query locali su DB indicizzato.
5. **Apertura file**: apertura con l'app di default del sistema operativo.

## Flusso online (aggiornamenti)
1. **Pull aggiornamenti**: sync periodica da fonte online configurata.
2. **Confronto versioni**: confronto `versione`/`data_pubblicazione`.
3. **Gestione superati**: spostamento file obsoleti in `/SUP`.
4. **Notifica**: avviso in UI con log dettagliato delle modifiche.

## UI/UX
- **Sidebar filtri**: categorie, tag, stato, range date.
- **Vista elenco per categoria**: group header + count per categoria.
- **Scheda dettaglio**: metadati, tag, versioni e azioni file.
- **Import/Export**: wizard di import e pulsante export .txt.
- **Indicatori stato**: badge `attiva/superata`, ultima versione evidenziata.

## Gestione locale dei file
- Directory base scelta dall'utente.
- Struttura dei file:
  - `/Normative/[categoria]/[normativa]/` per le versioni attive.
  - `/Normative/[categoria]/[normativa]/SUP/` per le versioni superate.
- Il sistema mantiene il riferimento al file corrente e archivia le versioni precedenti.

## Requisiti non funzionali
- **Offline-first**: tutte le funzionalità principali disponibili senza rete.
- **Indicizzazione locale**: creazione di indici locali per ricerca e filtri rapidi.
- **Backup**: meccanismi di backup configurabili dall'utente.
- **Logging attività**: registrazione di operazioni chiave (import, update, export).
- **Validazione input**: controllo dei campi obbligatori e formati coerenti.
