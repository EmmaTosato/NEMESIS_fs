---
name: stato-progetto
description: Aggiorna .claude/stato_progetto.md con un riassunto tecnico della sessione corrente (decisioni prese, file modificati, concetti discussi, errori trovati, stato test, prossimo passo esatto). Usa questa skill quando l'utente chiede esplicitamente di salvare/aggiornare lo stato del progetto, o quando avvisa che la chat sta per essere resettata/compattata.
---

# Checkpoint: stato_progetto.md

`stato_progetto.md` è **cumulativo e cronologico inverso**: copre più sessioni, la più recente in cima. A differenza di un file "stato attuale" che si riscrive da zero, qui **non si cancella mai nulla** — si aggiunge una nuova sezione in testa, le sessioni precedenti restano intatte per lo storico. Lo scopo è permettere a un nuovo agente/sessione, senza alcun contesto pregresso, di riprendere esattamente da dove ci si è fermati.

## Procedura

1. **Leggi** `.claude/stato_progetto.md` se esiste. Se non esiste, crealo con intestazione:
   ```
   # Stato progetto — NEMESIS

   Ultimo aggiornamento: YYYY-MM-DD. Scritto per permettere a un nuovo agente/sessione di riprendere senza contesto pregresso. Il file copre più sessioni, in ordine cronologico inverso (la più recente in cima).
   ```

2. **Determina il titolo della nuova sezione**: `## Sessione YYYY-MM-DD [(N)] — <titolo breve>`.
   - Data odierna assoluta (non relativa).
   - Se è già presente in cima una sezione con la stessa data, questa è la sessione successiva dello stesso giorno → aggiungi il suffisso numerico `(2)`, `(3)`, ecc. Se è la prima del giorno, nessun suffisso.
   - Titolo breve = argomento principale affrontato (es. "SDC/BCBToolKit: blocco permessi e mappatura pipeline del paper"), non generico ("lavoro vario").

3. **Inserisci la nuova sezione subito dopo la riga "Ultimo aggiornamento"**, prima di tutte le sessioni precedenti. Aggiorna anche la data in quella riga.

4. **Contenuto della sezione** — ricostruiscilo dalla conversazione corrente e, dove possibile, verifica sul filesystem invece di fidarti solo della memoria della chat (`git status`, `git diff`, `ls`):
   - **Obiettivo**: cosa si stava cercando di fare, 1-3 frasi.
   - **Decisioni prese / concetti discussi**: le scelte fatte (architetturali, di design, di scope) **con la motivazione** — il "perché", non solo il "cosa". Se una decisione precedente è stata cambiata o scartata in questa sessione, dillo esplicitamente (non lasciare che sembri sempre stata così).
   - **File modificati/creati**: elenco per categoria (codice, config, test, doc) — controlla con `git status`/`git diff`, non elencare a memoria.
   - **Errori trovati e corretti**: riassunto sintetico se ce ne sono stati; se esiste già un debug report dedicato per la sessione, rimanda lì per il dettaglio invece di duplicarlo qui.
   - **Stato dei test**: conteggio esatto se rilanciati (es. "70/70 passano"), oppure nota esplicita se non sono stati rilanciati e perché.
   - **Prossimo passo esatto**: azione concreta, specifica, azionabile subito — non "continuare il lavoro". Deve bastare a un agente senza contesto per sapere cosa fare per primo.

5. **Sii tecnico e conciso**: questo file lo legge un agente, non un umano che vuole prosa piacevole. Evita di ripetere tra sezioni la stessa informazione. Ometti sezioni vuote invece di scrivere "nessuno".

6. **Non toccare le sessioni precedenti** già presenti nel file: restano intatte, anche se ora sai che una decisione lì descritta è stata superata — in quel caso lo segnali nella *nuova* sezione, non modifichi la vecchia.

7. Se in questa sessione sono emersi **pattern di errore generalizzabili** (non specifici al task del giorno, ma riutilizzabili — es. un tipo di bug che potrebbe ripetersi altrove), verifica se vanno aggiunti anche a `.claude/lessons_learned.md`: quello è l'indice dei pattern, `stato_progetto.md` è il diario di sessione. Non duplicare contenuto tra i due file.
