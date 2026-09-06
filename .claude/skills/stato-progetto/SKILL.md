---
name: stato-progetto
description: Aggiorna .claude/stato_progetto.md con uno snapshot tecnico dello stato attuale del progetto (architettura, lavoro attivo, vincoli in vigore, prossimo passo esatto). Usa questa skill quando l'utente chiede esplicitamente di salvare/aggiornare lo stato del progetto, o quando avvisa che la chat sta per essere resettata/compattata.
---

# Checkpoint: stato_progetto.md

`stato_progetto.md` è uno **snapshot puro dello stato attuale** — non un log cronologico, non un diario di sessione. Si **riscrive in place** ogni volta: non si aggiunge una nuova sezione, non si accumula nulla, il contenuto precedente viene sostituito da quello che è vero *ora*. Lo scopo è permettere a un nuovo agente/sessione, senza alcun contesto pregresso, di sapere rapidamente dove si trova il progetto oggi — non di ricostruire come ci si è arrivati.

**La narrativa di cosa è successo sessione per sessione non va qui.** È già coperta altrove — non duplicarla:
- **git log / commit message** — cosa è cambiato nel codice, quando, perché (a livello di dettaglio tecnico di un singolo cambio).
- **`docs/debugging/debug_DD_MM_YY.md`** — narrativa completa di una sessione di debug con bug reali trovati.
- **`.claude/history/`** — l'archivio: cosa è successo ai dati, ai metodi, all'impianto del progetto (vedi la skill `history`).
- **`.claude/lessons_learned.md`** — pattern di errore generalizzabili, deduplicati.
- **`runs.csv`/`runs_tuning.csv` + `logs/`/`summaries/`** — provenienza di ogni esecuzione di pipeline (parametri, output, log grezzo), già machine-written.
- **`.claude/history/stato_progetto_archive.md`** — storico congelato delle sessioni registrate prima del 2026-08-10 (quando questo file era ancora un log cronologico); sola lettura, non toccarlo.

Se un'informazione ha già una casa in uno di questi posti, in `stato_progetto.md` ci va **solo un puntatore**, non il contenuto.

## Procedura

1. **Leggi** `.claude/stato_progetto.md` se esiste. Se non esiste, crealo con la struttura del passo 3.

2. **Verifica sul filesystem, non a memoria**: `git status`/`git log`/`ls` per capire cosa è effettivamente cambiato prima di scrivere qualunque affermazione su file modificati o lavoro fatto.

3. **Riscrivi l'intero file** (non appendere) con questa struttura:
   ```
   # Stato progetto — NEMESIS

   Ultimo aggiornamento: YYYY-MM-DD. Snapshot dello stato attuale — non un log cronologico. [...]

   ## Architettura / cosa è implementato
   [puntatore a README.md/docs/dev/, non ripetere il contenuto]

   ## Lavoro attivo / thread aperti
   [cosa è in corso *ora*, non cosa è stato fatto in passato]

   ## Vincoli/regole in vigore oggi
   [regole operative attuali - solo quelle che cambiano il comportamento di un agente che riprende il lavoro]

   ## Prossimo passo esatto
   [azione concreta, specifica, azionabile subito - non "continuare il lavoro"]
   ```

4. **Contenuto di ogni sezione**:
   - **Architettura / cosa è implementato**: un puntatore a `README.md`/`docs/dev/`, non una ricostruzione — se stai per scrivere più di 1-2 righe qui, quell'informazione appartiene a `docs/`, non a questo file.
   - **Lavoro attivo / thread aperti**: solo ciò che non è ancora concluso — task/piani a metà, decisioni prese ma non ancora implementate. Se un thread si è chiuso in questa sessione, rimuovilo, non lasciarlo come "fatto" (git log lo prova già).
   - **Vincoli/regole in vigore oggi**: solo regole operative che cambiano il comportamento di un agente che riprende — non rifare l'inventario di `code_standards.md`/`CLAUDE.md`, solo eccezioni/vincoli specifici del momento (es. "lavoro su branch X", "server Y irraggiungibile", "modalità locale non SLURM").
   - **Prossimo passo esatto**: azione concreta, specifica, azionabile subito — non "continuare il lavoro". Deve bastare a un agente senza contesto per sapere cosa fare per primo.

5. **Sii tecnico e conciso**: questo file lo legge un agente, non un umano che vuole prosa piacevole. Ometti sezioni vuote invece di scrivere "nessuno". Se una sezione esistente è ormai falsa/superata (thread chiuso, vincolo caduto), **cancellala**, non annotarla come storica — per quello c'è l'archivio/git log.

6. Se in questa sessione sono emersi **pattern di errore generalizzabili** (non specifici al task del giorno, ma riutilizzabili — es. un tipo di bug che potrebbe ripetersi altrove), verifica se vanno aggiunti a `.claude/lessons_learned.md`. Se è successo qualcosa che va **archiviato** (ai dati, ai metodi, all'impianto del progetto), usa la skill `history`. Non duplicare contenuto tra questi file e lo snapshot.
