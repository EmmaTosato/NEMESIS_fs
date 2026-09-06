---
name: history
description: Archivia in .claude/history/ un cambiamento avvenuto — ai dati, ai metodi di analisi o all'impianto del progetto — instradandolo nel file giusto. Usa questa skill quando è appena successo qualcosa che va ricordato ma che non è né codice (già in git) né una run di pipeline (già in runs.csv), o quando l'utente chiede di archiviare/registrare cosa è stato fatto.
---

# Archiviare in `.claude/history/`

`docs/` descrive **il presente**. Tutto ciò che è "com'era prima", "cosa è successo", "perché siamo arrivati qui" non va lì: va in `.claude/history/`.

Questa skill decide **in quale file** e **cosa scriverci**.

## Prima di tutto: va archiviato davvero?

Molto di ciò che sembra storia ha già una casa migliore. **Non archiviare qui**:

| Se è… | Sta già in… |
|---|---|
| una modifica al codice | `git log` — non duplicarla mai |
| una run di pipeline (parametri, output, durata) | `runs.csv` + `logs/`/`summaries/` |
| un bug trovato e risolto in una sessione di debug | `docs/debugging/debug_DD_MM_YY.md` |
| un pattern di errore riutilizzabile altrove | `.claude/lessons_learned.md` |
| cosa è in corso *adesso* | `.claude/stato_progetto.md` (skill `stato-progetto`) |
| il risultato di un esperimento/analisi | `docs/experiments/` |

Se rientra in una di queste righe, **fermati e scrivi lì**, non qui.

## Instradamento

Una sola domanda, in quest'ordine:

1. **Sono cambiati i byte sotto `data/`?** → `data_changelog.md`
   Trasferimenti, potature/ripristini di archivi, spostamenti, rinomine, cancellazioni, correzioni sul posto (una colonna di un tsv rinominata, un file sostituito). Esiste perché `data/` è gitignored: `git log` non ne sa nulla.
   Ci va anche il caso in cui **una pipeline ha prodotto output sbagliato a causa dello stato dei dati** (non per un bug di codice — quello è `docs/debugging/`).

2. **Abbiamo deciso *come analizzare*?** → `methods_changelog.md`
   Scelte metodologiche/scientifiche e le loro alternative scartate: usare un proxy per una variabile mancante, calcolare una feature geometricamente invece di leggerla, fissare una soglia, scegliere un target di ricampionamento, adottare/abbandonare un metodo.

3. **Abbiamo deciso *come è organizzato il progetto*?** → `project_changelog.md`
   Scelte di impianto: una fonte di verità unica al posto di N file, ritiro di una pipeline, split di uno script in due, cambio di convenzione di naming, cambio di formato di un artefatto.

Se un evento tocca due categorie, scrivilo **una volta sola** nella più specifica e, se serve, rimanda con una riga. Non spaccare il capello: meglio una voce nel file quasi-giusto che due voci che divergono.

`stato_progetto_archive.md` è **sola lettura**: narrativa congelata di sessioni vecchie, non ci si aggiunge mai niente.

I file si creano alla prima voce che serve — non pre-crearli vuoti.

## Quando scrivere

**Nello stesso turno dell'azione, non a fine sessione.** Ricostruire dopo, a memoria, è il modo in cui i dettagli si perdono: il numero esatto, quale tentativo era fallito, cosa era stato scartato e perché.

## Come scrivere una voce

Una sezione per evento, **la più recente in cima**, sotto l'intestazione del file:

```markdown
## GG-MM-AA — titolo breve di cosa è successo

Cosa è cambiato, in concreto (numeri veri, non "alcuni file").

Perché, se non è ovvio. Le alternative scartate e il motivo, se la decisione
potrebbe essere rimessa in discussione più avanti.

La conseguenza ancora vera oggi, se c'è — quella che farebbe sbagliare
qualcuno che non conosce questa storia.
```

Regole:
- **Numeri verificati, non ricordati**: controlla su disco/git prima di scrivere una cifra.
- **Niente prosa di cortesia**: lo legge un agente senza contesto, non un umano che vuole un racconto.
- **Un evento, una voce**: non accorpare tre cose scollegate in un paragrafo.
- Se la voce descrive una decisione **ancora in vigore**, la regola va anche in `docs/` (al presente, senza date) — qui resta il *perché* e cosa è stato scartato.

## Procedura

1. Verifica sul filesystem cosa è effettivamente successo (`git status`, `ls`, conteggi reali) — mai a memoria.
2. Instrada con le 3 domande sopra; se nessuna si applica, la voce non va in `history/`.
3. Leggi il file di destinazione, se esiste, per non ripetere una voce già presente.
4. Scrivi la voce in cima (dopo l'intestazione), nel formato sopra.
5. Se lo stesso fatto ha una conseguenza attuale, aggiorna anche `docs/` — ma al presente, senza date né cronaca.
