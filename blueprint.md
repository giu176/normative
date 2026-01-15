# Blueprint

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
