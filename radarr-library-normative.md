---
title: Normative Library
description: Gestisci la collezione di normative, monitora lo stato e organizza la libreria locale
published: true
date: 2024-01-01T10:00:00.000Z
tags: normative, library, gestione, collezione, organizzazione, monitoring
editor: markdown
dateCreated: 2024-01-01T10:00:00.000Z
---

# Normative

## Vista Libreria

- Aggiorna tutto - Aggiorna metadati di tutte le normative, rigenera copertine/anteprime (se presenti), riconsidera cartelle e file locali.
- Aggiorna & Scansiona - Aggiorna i metadati della normativa corrente e riscansiona la sua cartella.
- Sync Feed - Aggiorna il feed dalle fonti configurate (API o scraping) e verifica nuove pubblicazioni.
- Cerca Tutto / Cerca Filtrate / Cerca Selezionate - Cerca tutte le normative o solo quelle filtrate nella vista corrente.
- Import Manuale (Indice) - Importa manualmente un file normativa per una normativa già aggiunta, da qualunque cartella accessibile.
  - Sposta automaticamente - Tenta di riconciliare il file con una normativa e importarlo spostandolo.
  - Import interattivo - Mostra i file nel percorso, prova l’associazione con una normativa e consente revisione. Sposta o Copia/Hardlink selezionabili.
- Import Manuale (Normativa) - Importa manualmente un file per la normativa selezionata dalla cartella assegnata.
  - Sposta automaticamente - Tenta di riconciliare il file con una normativa e importarlo spostandolo.
  - Import interattivo - Mostra i file nel percorso, prova l’associazione con una normativa e consente revisione. Sposta o Copia/Hardlink selezionabili.
- Editor Normative / Indice - Alterna tra modalità Mass Editor e modalità indice (libreria).
- Opzioni - Cambia opzioni di visualizzazione.
- Vista - Cambia il tipo di vista
  - Tabella - Vista tabellare (lista)
  - Schede - Vista con card e anteprima file
  - Dettaglio - Vista dettagliata con metadati, tag e stato
- Ordina - Ordina la vista corrente

### Filtri

- Filtro - Filtra la vista corrente
  - Monitorate - Normative monitorate per aggiornamenti.
  - Non monitorate - Normative NON monitorate.
  - Mancanti - Presenti in database ma senza file locale associato.
  - Attese - Monitorate, mancanti, ma attese in base alle fonti configurate.
  - Versione non soddisfatta - File presente, ma esiste una versione più recente attesa.
  - Filtri personalizzati
    - Monitorata (boolean)
    - Disponibile (boolean)
    - Disponibilità minima (Enum)
      - Annunciata
      - In consultazione
      - Pubblicata
    - Titolo [contiene] (String)
    - Stato (Enum)
      - In bozza
      - Annunciata
      - In consultazione
      - Pubblicata
      - Abrogata
    - Ente (Enum Enti)
    - Raccolta (Enum Collezioni)
    - Profilo Qualità (Enum Profili)
    - Aggiunta (DateTime, TimeDelta)
    - Anno (Int)
    - Data pubblicazione (DateTime, TimeDelta)
    - Data entrata in vigore (DateTime, TimeDelta)
    - Data ultimo aggiornamento (DateTime, TimeDelta)
    - Percorso [contiene] (String)
    - Dimensione su disco (Int)
    - Tag [contiene] (Enum Tag)
    - Fonte (Enum Fonti)
    - Revisione (String)
    - Note [contiene] (String)

# Aggiungi Nuova

![normative-add-new-empty.png](/assets/normative/normative-add-new-empty.png)

- Per aggiungere una nuova normativa, questa è la pagina di riferimento.
  - Qui trovi la guida rapida in [Quick Start Guide](/normative/quick-start-guide).
- Sotto il campo di ricerca trovi il pulsante Importa Libreria Esistente. Dettagli nella [Quick Start Guide](/normative/quick-start-guide).
- Se ottieni l’errore "percorso già configurato", [vedi la FAQ](/normative/faq#path-is-already-configured-for-an-existing-normativa).

# Import Libreria

L’Import Libreria consente di importare normative già organizzate e i relativi file tramite cartelle esistenti. È utile per nuove installazioni in cui vuoi mantenere l’archivio locale.

- L’import libreria serve per aggiungere e importare una libreria esistente di normative organizzate.
- L’import libreria NON può essere usato per:
  - Importare file da una cartella di download temporanea
  - Aggiungere o importare file non nominati e organizzati correttamente in una cartella dedicata alla normativa
  - Qualsiasi altro uso che non sia aggiungere una normativa e importare il file dalla cartella root indicata
- Se ottieni l’errore "percorso già configurato", [vedi la FAQ](/normative/faq#path-is-already-configured-for-an-existing-normativa).

> È richiesto che le cartelle delle normative e i file contengano l’anno nel nome per essere importati e interpretati.{.is-warning}

> * Non-Windows: se usi un mount NFS assicurati che `nolock` sia abilitato.
> * Se usi un mount SMB assicurati che `nobrl` sia abilitato.
{.is-warning}

> **L’utente e il gruppo con cui gira il servizio devono avere permessi di lettura e scrittura sulla posizione indicata.**
{.is-info}

> Il client di acquisizione deposita i file in una cartella di download e il sistema li importa nella cartella media (destinazione finale) usata dalla libreria.
{.is-info}

> **La cartella di download e la cartella della libreria non possono essere la stessa posizione**
{.is-danger}

# Collezioni

La wiki è sviluppata e mantenuta dalla community.
Questa sezione non ha ancora contributi che descrivano la pagina Collezioni per le normative.

# Scopri

Scopri mostra normative consigliate.

- Se non hai liste, mostra le normative più raccomandate in base a quelle già presenti in libreria e agli ultimi inserimenti.

> Suggerimento: puoi disattivare le raccomandazioni e vedere solo le normative delle tue liste in `Opzioni`.
{.is-info}

- Se hai liste, mostra le raccomandazioni e anche le voci dalle liste configurate.

> Suggerimento: imposta il filtro `Nuove non escluse` per vedere solo normative non presenti in libreria.
{.is-info}

![normative-discover-empty.png](/assets/normative/normative-discover-empty.png)

- È normale avere poche raccomandazioni in una nuova installazione. Puoi alimentare i suggerimenti in tre modi:
  1. Clicca su [Aggiungi Nuova Normativa](/normative/library#aggiungi-nuova).
  1. Clicca su [Importa Libreria Esistente](/normative/library#import-libreria).
  1. Clicca su [Aggiungi Liste](/normative/settings#liste). Maggiori info su [Liste supportate](/normative/faq#cosa-sono-le-liste).

![normative-discover-add-new.png](/assets/normative/normative-discover-add-new.png)

- Dopo aver aggiunto normative, vedrai nuovi suggerimenti:
  1. Seleziona quali normative aggiungere alla libreria.
  1. Seleziona tutte le normative della lista (opzione bulk).
  1. Seleziona il percorso root di destinazione.
  1. Seleziona la disponibilità minima prima dell’import.
  1. Seleziona un profilo qualità/configurazione.
  1. Scegli se monitorare aggiornamenti futuri.
  1. Scegli se cercare automaticamente dopo l’aggiunta.
  1. Escludi le normative da liste future, se necessario.
  1. Infine aggiungi la normativa alla libreria.
