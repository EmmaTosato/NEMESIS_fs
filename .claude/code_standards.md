# Standard di codice — NEMESIS

Regole per il codice in `src/`, `scripts/` (e i relativi test), valide non appena il progetto smette di essere solo notebook/esplorazione.

---

## 0. Principio cardine: niente fallback silenziosi

**Non voglio fallback.** Ogni caso limite (input mancante, file assente, formato inatteso, combinazione impossibile) deve essere **gestito esplicitamente**:

- o si solleva un errore chiaro (`raise ValueError(...)`, `raise FileNotFoundError(...)`, ecc.) con un messaggio che dice *cosa* manca e *perché* è un problema,
- o si gestisce il caso con una strategia reale e intenzionale (es. un valore di default motivato, un ramo alternativo documentato) — **mai** una toppa che nasconde il problema (`.get(key, {})` su un campo obbligatorio, `except: pass`, `if x is None: return None` senza spiegazione).

**Non va bene:**
```python
def lesion_mask(self, subject_id):
    try:
        return self._resolve(subject_id)
    except Exception:
        return None  # nasconde il problema, il chiamante non sa perché
```

**Va bene:**
```python
def lesion_mask(self, subject_id: str) -> Path | None:
    if not self.has_derivatives():
        raise ValueError(f"il dataset {self.name!r} non contiene derivatives (manual_masks)")
    ...
    return match  # None è un caso legittimo e documentato (manca per QUEL soggetto), non un errore nascosto
```

Questo principio ha priorità su tutti gli altri: in caso di dubbio tra "far fallire rumorosamente" e "andare avanti comunque", si fallisce rumorosamente.

---

## 1. Architettura del codice

| Regola | Dettaglio |
|---|---|
| Struttura a livelli | `utils` → `preprocessing`/`retrieval` → `features` → `models`/`analysis` → `pipeline`. I livelli alti dipendono da quelli bassi, mai il contrario |
| Una responsabilità per modulo | No classi che fanno tutto (I/O + logica + metriche insieme) |
| No stato globale | Niente variabili a livello di modulo che persistono tra chiamate; dipendenze passate come argomenti |
| Composizione > ereditarietà | Preferire wrapping/composizione a gerarchie di classi profonde (>3-4 livelli) |
| Entry point centralizzati | Punto d'ingresso unico in `src/pipeline/`, niente script sparsi |

---

## 2. Qualità del codice

| Regola | Dettaglio |
|---|---|
| Type hints ovunque | Ogni funzione/metodo pubblico ha tipi su parametri e ritorno |
| Funzioni piccole | Una responsabilità, idealmente <30 righe; nomi che descrivono cosa fanno. Il limite vale per funzione/metodo, non per la classe nel suo complesso: una classe con molti metodi piccoli e coesi va bene |
| Nomi chiari | No abbreviazioni oscure; ok abbreviazioni standard di dominio (SDC, ROI, MNI...) |
| Niente codice morto | Funzioni/classi/import non usati si cancellano subito — verificare con `grep -rn` prima di eliminare, mai lasciare "per sicurezza" |
| Niente shim di compatibilità | No wrapper "per i vecchi chiamanti", no `# rimosso` in commento, no stub di funzioni eliminate |

---

## 3. Gestione errori (si lega al §0)

- Mai `except:` nudo o `except Exception: pass`
- Catturare eccezioni specifiche, non generiche
- Ogni eccezione sollevata ha un messaggio che identifica cosa è andato storto e con quale input
- Un `None` di ritorno è accettabile solo se è un **caso di dominio legittimo e documentato** (es. "questo soggetto non ha questo file"), non un modo per evitare di sollevare un errore

---

## 4. Testing

| Regola | Dettaglio |
|---|---|
| Organizzazione | `tests/unit/` (isolati) e `tests/integration/` (roundtrip), specchiando la struttura di `src/` |
| Regressione obbligatoria | Ogni bug fix ha un test che fallisce col codice vecchio e passa col nuovo |
| Almeno un E2E | Un test che copre il flusso completo con dati reali piccoli |
| Mock solo su I/O esterno | Mai mockare il codice sotto test; dati reali (piccoli) preferiti ai mock |
| Suite verde prima di chiudere | Dopo modifiche a `src/`, girare `pytest tests/ -v` e riportare il conteggio esatto (es. `12/12 passed`) |

---

## 5. Configurazione

- Nessun valore ambiente-dipendente hardcoded nel codice (path, soglie, iperparametri) → in `config/` o variabili d'ambiente
- Ogni valore in un solo posto (single source of truth)
- Commenti nei config solo se aggiungono informazione non deducibile dal nome del campo
- Niente campi di config non letti da nessun codice attivo (verificare con `grep -rn` prima di tenerli)

---

## 6. Logging

- Log in inglese, stile ibrido testo libero + `chiave=valore`
- Mai dati sensibili (credenziali, path con auth) nei log
- Ogni eccezione loggata con contesto completo (`exc_info=True`), mai in silenzio
- Livelli usati coerentemente: INFO (milestone), DEBUG (dettagli verbosi), WARNING (recuperabile), ERROR (richiede attenzione)

---

## 7. Documentazione

- Aggiornare `docs/` ad ogni cambio di interfaccia, config o workflow — comprese le rimozioni (una doc su qualcosa che non esiste più è peggio di nessuna doc)
- Tenere separati: come si usa (utente), come è strutturato (architettura), perché è fatto così (dettagli implementativi/algoritmici)

---

## 8. Debug report

- Un file per sessione di debug (`docs/debugging/debug_DD_MM_YY.md` se/quando la cartella esiste)
- Un bug per sezione, con livello di criticità e "lessons learned" obbligatorio (azionabile, non una parafrasi del bug) (`lesson_learned.md`)

---

## Riferimenti

- [`.claude/CLAUDE.md`](../.claude/CLAUDE.md) — struttura repo e convenzioni generali NEMESIS
- [`docs/notes/architecture_draft.md`](notes/architecture_draft.md) — bozza architettura pipeline (non normativa)
- [`src/retrieval.py`](../src/retrieval.py) — esempio attuale di gestione errori conforme al §0
