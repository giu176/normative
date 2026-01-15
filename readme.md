# Standarr self-hosted – Blueprint completa

## Avvio rapido (Docker Compose)

```bash
docker compose up --build
```

Servizi:

- API: http://localhost:8000
- UI: http://localhost:5173
- PostgreSQL: localhost:5432 (db: standarr, user: standarr, pass: standarr)

L'API espone gli endpoint principali per catalogo, list builder, export e ingestion.

## 1) Obiettivi e principi di progetto

### Obiettivi funzionali

- Biblioteca centralizzata di normative/standard (UE, Italia, ISO/IEC).
- Stato/versioning: “in vigore”, “ritirata”, “sostituita”, timeline.
- Filtri esaustivi per selezione norme applicabili.
- Generazione Elenco (bozza) da filtri, modificabile manualmente (add/remove).
- Export in TXT raggruppato per discipline con regola B.

### Principi non negoziabili

- Separazione netta metadati vs contenuti (PDF upload locali solo dell’utente).
- Provider ingestion disaccoppiati (plug-in).
- Query riproducibile: ogni elenco conserva i filtri e uno snapshot.

## 2) Architettura logica (moduli)

### 2.1 Core services

**Catalog Service**

- CRUD su Norme (Work) e Versioni (Edition)
- gestione stato e timeline
- gestione relazioni tra versioni

**Taxonomy Service**

- tassonomia “discipline” standard (gestita dall’istanza, con versionamento)
- mapping disciplina primaria + discipline secondarie (riferimenti)

**Tag Service**

- tag liberi per utente/istanza
- autocompletamento e merge

**Search Service**

- ricerca full-text su titolo/abstract
- filtri strutturati (authority, stato, date, discipline, tag, relazioni, disponibilità)
- backend: PostgreSQL FTS (prima versione) + opzionale OpenSearch (futuro)

**List Builder Service (feature principale)**

- definizione filtri → set automatico
- creazione NormativeList bozza
- override manuali: include/exclude e note
- rigenerazione preservando override

**Export Service**

- generazione file TXT secondo template
- raggruppamento per disciplina (primaria) + riferimenti per discipline secondarie (regola B)

**Ingestion Service**

- scheduler + coda job
- provider adapter (UE, IT, ISO/IEC)
- normalizzazione + matching/merge

**Attachment Service (opzionale, ma previsto)**

- upload PDF locale associato a Edition
- hashing, dedup, metadati file
- indicizzazione testo solo locale (se implementata)

### 2.2 Cross-cutting

- AuthN/AuthZ (anche semplice: admin + utenti locali; o solo admin inizialmente)
- Audit log (azioni su liste, override, import)
- Observability (log strutturati + healthcheck)

## 3) Stack tecnologico consigliato (pragmatico, self-hosted)

### Backend

- .NET (C#) o Node.js/TypeScript o Python (FastAPI): scegli in base al tuo team.
- DB: PostgreSQL.
- Job runner: Hangfire (se .NET) / BullMQ (Node) / Celery (Python).
- Storage allegati: filesystem locale o S3-compatible (MinIO).

### Frontend

- SPA: React/Vue + componenti tabella/filtri.
- UI pattern tipo arr: lista centrale + filtri laterali + dettagli in pannello.

### Deployment

- Docker Compose: api, ui, postgres, (opzionale opensearch), (opzionale minio).

## 4) Modello dati (schema concettuale)

### 4.1 Entità principali

**DisciplineCategory**

- id
- code (es. STR, ELE, FIRE)
- name
- version
- sort_order
- active

**UserTag**

- id
- name
- normalized_name
- created_at

**DocumentWork (norma “concetto”)**

- id
- authority (EU, IT, ISO, IEC, EN, UNI, CEI, …)
- identifier (stringa canonica: “ISO 9001” / “Reg. (UE) 2016/679”)
- title
- abstract (opzionale)
- primary_discipline_id
- created_at, updated_at

**WorkDiscipline (discipline secondarie)**

- work_id
- discipline_id

**WorkTag**

- work_id
- tag_id

**DocumentEdition (versione/edizione specifica)**

- id
- work_id
- edition_label (es. “2015”, “2020+A1:2024”)
- publication_date
- status (in_force, withdrawn, superseded, draft, unknown)
- valid_from, valid_to (nullable)
- source_canonical_url (opzionale)
- created_at, updated_at

**EditionRelation**

- id
- from_edition_id
- to_edition_id
- type (replaces, amends, corrigendum_of, adopted_as, etc.)
- confidence (0–1; utile se matching automatico)
- source (provider)

**SourceRecord**

- id
- provider (eurlex, normattiva, iso, manual, …)
- external_id (CELEX, id normattiva, ecc.)
- payload_hash
- fetched_at
- raw_reference (URL o stringa)
- work_id/edition_id (link)

**LocalAttachment**

- id
- edition_id
- filename
- mime_type
- size_bytes
- sha256
- storage_path
- uploaded_at

### 4.2 Liste (feature “elenco applicabile”)

**NormativeList**

- id
- name
- description
- status (draft, final)
- created_at, updated_at
- source_filter_json (snapshot dei filtri)
- regeneration_mode (dynamic, frozen)
- preserve_overrides (bool)

**NormativeListItem**

- id
- list_id
- edition_id (scelta consigliata: sempre Edition, non Work)
- included (bool)
- reason (auto, manual_include, manual_exclude)
- note (text)
- primary_discipline_id_at_time (snapshot per stabilità export)
- secondary_discipline_ids_at_time (snapshot; JSON)
- added_at

## 5) Logica disciplina primaria + riferimenti (regola B)

### Regola

- Ogni Work ha 1 disciplina primaria.
- Può avere 0..N discipline secondarie.

**Export**:

- nella sezione della disciplina primaria: entry completa
- nelle discipline secondarie: una riga di riferimento (es. “Vedi: [Disciplina primaria] – [Identificativo]”)

### Motivo

- Evita duplicati e “liste infinite”.
- Mantiene la tracciabilità.

## 6) Ricerca e filtri (specifica funzionale)

### Filtri supportati (MVP completo)

- Authority (multi-select)
- Tipo documento (se gestito)
- Stato: solo in vigore / includi ritirate / includi sostituite
- Date: pubblicazione (from/to), aggiornamento rilevato (from/to)
- Disciplina: primaria e/o secondarie
- Tag liberi (AND/OR)
- Relazioni:
  - includi ammendamenti/corrigenda associati
  - “solo ultima edizione in vigore”
- Disponibilità:
  - ha allegato locale
  - ha link ufficiale

### Comportamento ricerca

- Interattiva: aggiorna risultati e contatore.
- “Save filter preset”: salva set filtri come preset (opzionale).

## 7) List Builder (flusso dettagliato)

### 7.1 Creazione bozza

- utente imposta filtri
- preview risultati + selezione “solo ultima in vigore” (consigliato)
- click “Crea elenco”
- sistema:
  - esegue query
  - materializza items con reason=auto, included=true
  - snapshot discipline primaria/secondarie per stabilità

### 7.2 Revisione manuale (obbligatoria prima export)

- tabella per disciplina (primaria) con:
  - toggle included
  - campo note
  - ricerca per aggiungere manualmente una Edition (autocomplete)
  - “riferimenti” nelle discipline secondarie mostrati separatamente (non duplicano)
- possibilità “blocca elenco” (status=final) per congelarlo

### 7.3 Rigenerazione

- se l’utente rigenera dalla query:
  - ricalcola auto-set
  - applica override:
    - manual_exclude resta escluso
    - manual_include resta incluso
  - segnala nuovi items auto rispetto alla versione precedente

## 8) Export TXT (specifica formato)

### Struttura proposta

- Header con metadata elenco
- Sezioni per disciplina primaria in ordine
- Dentro ogni disciplina:
  - “Norme (primarie)”
  - “Riferimenti (secondarie)”

**Esempio (schema):**

```
Standarr – Elenco Normative
Nome elenco: <name>
Generato: <YYYY-MM-DD HH:MM>
Modalità: Frozen/Dynamic
Criteri (snapshot): <riassunto filtri>

== STRUTTURE ==
[Norme]
- <IDENTIFIER> — <TITLE> (Ed. <edition_label>, Pub. <date>) [Authority] <STATUS>
  Note: <note se presente>

[Riferimenti]
- <IDENTIFIER> — vedi disciplina primaria: <PRIMARY_DISCIPLINE_NAME>

== IMPIANTI ELETTRICI ==
...
```

Regola B applicata nei “Riferimenti”.

## 9) API interne (contract indicativo)

### Catalog

- GET /api/works?filters...
- GET /api/works/{id}
- GET /api/editions/{id}
- POST /api/works (manual entry)
- POST /api/editions (manual entry)
- POST /api/relations

### Liste

- POST /api/lists (crea bozza da filtri)
- GET /api/lists/{id}
- PATCH /api/lists/{id} (nome/descrizione/status)
- POST /api/lists/{id}/regenerate
- POST /api/lists/{id}/items/{itemId}/include|exclude
- POST /api/lists/{id}/items/manual-add (edition_id + discipline snapshot)
- PATCH /api/lists/{id}/items/{itemId} (note)

### Export

- GET /api/lists/{id}/export/txt (stream file)

### Ingestion

- POST /api/ingestion/run?provider=...
- GET /api/ingestion/status

## 10) Ingestion blueprint (provider pattern)

### Interfaccia provider (concetto)

- FetchChanges(since) → elenco record esterni
- GetDetails(external_id) → metadati completi + relazioni + link
- Normalize(record) → WorkCandidate, EditionCandidate, Relations
- MatchAndMerge(candidate):
  - match per identifier canonico (con normalizzazione)
  - fallback: fuzzy match su titolo + authority + date
  - assegnazione confidence
- Persist() + Index()

### Matching: regole MVP

- Canonicalizzazione identifier (spazi, trattini, prefissi).
- Per atti UE: chiave forte = CELEX (quando presente).
- Per atti IT: chiave forte = id Normattiva o estremi.
- Per ISO/IEC: chiave forte = codice standard + edition_label.

## 11) UI blueprint (pagine)

### Library

- tabella: Identifier, Title, Authority, Status, Primary discipline, Latest edition date
- filtri avanzati (accordion)
- azioni: “Apri”, “Aggiungi a elenco…”

### Work detail

- header + tag + discipline
- timeline edizioni (tabella)
- grafo relazioni (fase 2)

### List Builder

- step 1: filtri + preview count
- step 2: bozza per discipline (tab)
- inclusione/esclusione
- note
- aggiunta manuale
- step 3: export

### Ingestion / Admin

- stato provider
- ultimo run, errori, log

## 12) Roadmap (MVP → v1)

### MVP (rilascio utilizzabile)

- Catalog manuale + import base
- Discipline standard + tag liberi
- Ricerca + filtri principali
- Liste bozza + override manuali
- Export TXT
- Ingestion UE/IT “metadati-first” (anche solo parziale) + ISO metadati manuali

### v1

- Preset filtri
- Alert “cambiamenti”
- Allegati + indicizzazione locale
- Provider più completi + riconciliazione relazioni avanzata
- UI grafo relazioni

## 13) Requisiti non funzionali (self-hosted)

- Backup: dump PostgreSQL + cartella allegati.
- Migrazioni DB: tool migration (Flyway/Liquibase/EF migrations).
- Performance: caching query filtri + paginazione.
- Sicurezza: account locale + password hash, limit upload, path traversal safe.
