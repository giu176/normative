# Fonti normative e accesso

## 1) Gazzetta Ufficiale Italiana
- **Tipo di accesso**: portale web ufficiale; verificare disponibilità di API/OPAC. In assenza di API pubbliche, usare scraping mirato alle pagine di consultazione e ai metadati.  
- **Dati disponibili**: metadati di pubblicazione (numero, data, serie), titolo, sommario/estratto, link alla pubblicazione o al fascicolo.  
- **Limitazioni legali/licensing**: verificare termini d’uso del portale; possibile limitazione su frequenza di accesso e riutilizzo. I testi integrali potrebbero avere restrizioni di riuso o condizioni specifiche.

## 2) EUR-Lex
- **Tipo di accesso**: API ufficiali e documenti in XML/HTML. Disponibili endpoint di ricerca e accesso ai documenti.  
- **Dati disponibili**: metadati completi (CELEX, titolo, data, tipo atto), versioni consolidate, link a documenti e formati.  
- **Limitazioni legali/licensing**: dati generalmente riutilizzabili con licenze aperte UE; verificare condizioni di riuso e attribuzione.

## 3) ISO
- **Tipo di accesso**: catalogo norme con accesso spesso a pagamento; possibili metadati accessibili via portale o feed.  
- **Dati disponibili**: metadati di base (codice norma, titolo, stato, data pubblicazione, ente). Accesso al testo integrale generalmente a pagamento.  
- **Limitazioni legali/licensing**: forte restrizione sul testo integrale; uso limitato ai metadati pubblici. Verificare condizioni di riuso.

## 4) IEC/CEI
- **Tipo di accesso**: cataloghi con accesso spesso a pagamento; verificare disponibilità di metadati pubblici.  
- **Dati disponibili**: metadati di base (codice norma, titolo, stato, data pubblicazione, ente). Testo completo di norma con paywall.  
- **Limitazioni legali/licensing**: testo integrale in genere non riutilizzabile senza licenza; possibile uso dei soli metadati.

---

# Microservizio di scraping (quando API assenti o limitate)

## Architettura proposta
- **Scheduler**: job periodici (es. daily/weekly) per aggiornare metadati da fonti non-API.
- **Parser & normalizzazione**:
  - Campi normalizzati: **codice_norma**, **titolo**, **ente**, **data_pubblicazione**, **versione**, **stato**.
  - Regole di mapping per ogni fonte (es. CELEX, numero GU, codici ISO/IEC/CEI).
- **Storage**: database locale o file JSON/SQLite per caching risultati.
- **REST API read-only**:
  - `GET /sources` elenco fonti.
  - `GET /normative?source=&query=&status=` ricerca metadati.
  - `GET /normative/{id}` dettaglio norma con link e versione.

## Comportamento offline
- Cache locale aggiornata dallo scheduler.
- Se la fonte non è disponibile, il sistema usa l’ultimo snapshot.

---

# Repository “git-like” read-only per versionamento

## Schema di versionamento
- **Identificatore stabile**: `source + codice_norma` (es. `eurlex:32016R0679`).
- **Versione**: numero revisione o data di consolidamento.
- **Stato**: `attiva`, `superata`.
- **Struttura storage**:
  - `norme/<source>/<codice_norma>/metadata.json`
  - `norme/<source>/<codice_norma>/versions/<versione>.json`

## Endpoint di sincronizzazione (pull)
- `GET /sync?since=<timestamp>`: ritorna delta di metadati e nuove versioni.
- `GET /norme/<source>/<codice_norma>`: dettaglio con storico versioni.
- **Segnalazione versioni superate**: campo `stato` aggiornato e lista delle versioni sostituite.

---

# Gestione documenti non scaricabili automaticamente

- **Solo metadati**: si registra la scheda completa ma senza allegato.
- **Flag “manual download”**: indica che il testo integrale va acquisito manualmente.
- **Workflow di upload**:
  1. Acquisto/ottenimento licenza.
  2. Upload manuale del file nel repository locale.
  3. Collegamento del file ai metadati con `path_file_locale`.
- **Tracciamento**: log della provenienza (data, fornitore, licenza) per auditing.
