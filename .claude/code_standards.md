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
def group_of(subject_id: str) -> str:  # src/utils/subject_ids.py
    match = _SUBJECT_RE.fullmatch(subject_id)
    if match is None:
        raise ValueError(f"subject_id does not match expected naming: {subject_id!r}")
    return "HC" if match.group("hc") else match.group("disease")
    # un ID malformato, o di un sito non registrato in KNOWN_SITES, solleva: il gruppo non viene mai indovinato
```

**Eccezione dichiarata**: la scrittura dei grafici di embedding (`src/analysis/embedding_plots.py`). Un grafico è un prodotto ausiliario di una run che ha già salvato i suoi artefatti: se non si scrive per un errore atteso (`OSError`, `ValueError`) si logga un WARNING con il conteggio dei grafici mancanti e la run prosegue. Ogni altra eccezione è un bug e ferma la run.

Questo principio ha priorità su tutti gli altri: in caso di dubbio tra "far fallire rumorosamente" e "andare avanti comunque", si fallisce rumorosamente.

---

## 1. Architettura del codice

| Regola | Dettaglio |
|---|---|
| Struttura a livelli | `utils` → `features` → `analysis` → `pipeline`. I livelli alti dipendono da quelli bassi, mai il contrario |
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
| Codice parcheggiato | Codice non più chiamato da nessuno ma da tenere recuperabile si sposta in `tests/legacy/` insieme ai suoi test (non raccolti da pytest, eseguibili per percorso), non resta in `src/`. Unica eccezione dichiarata: la sezione «Confronto» (`src/analysis/embedding_app/panels/comparison.py`, `src/analysis/embedding_app/panels/cluster_pair.py`) (builder e test restano al loro posto, non montata nell'app) |
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
| Mock solo su I/O esterno | Mai mockare il codice sotto test; dati reali (piccoli) preferiti ai mock. Sostituire una funzione del repo è ammesso solo se non è il soggetto del test e rientra in un caso: una **spia** che registra la chiamata e poi esegue la funzione vera; l'**iniezione di un errore** per provare il confine di errore del chiamante; una dipendenza che nei test non può girare (il server Dash di `embedding_app`). Un ramo interno si raggiunge con dati che lo attivano, non sostituendo l'helper che lo sceglie |
| Suite verde prima di chiudere | Dopo modifiche a `src/`, girare `pytest tests/ -v` e riportare il conteggio esatto (es. `12/12 passed`) |

---

## 5. Configurazione

- Nessun valore ambiente-dipendente hardcoded nel codice (path, soglie, iperparametri) → in `config/` o variabili d'ambiente
- Ogni valore in un solo posto (single source of truth)
- Commenti nei config solo se aggiungono informazione non deducibile dal nome del campo
- Niente campi di config non letti da nessun codice attivo (verificare con `grep -rn` prima di tenerli)
- **Eccezioni dichiarate** (valori che non dipendono dall'ambiente di esecuzione o che sono per natura legati a una macchina):
  - Log e report di una pipeline stanno in `logs/<nome>/` e `summaries/<nome>/` (e i metadati in `assets/metadata`), relativi alla radice del repo: costanti di modulo (`LOGS_ROOT`, `REPORTS_ROOT`, `METADATA_ROOT`). Sono la struttura del repo, uguale su ogni macchina; i test le sostituiscono con `tmp_path`.
  - `jobs/*.sh` contengono i percorsi del cluster (progetto, `conda.sh`, log SLURM): sono script di una macchina precisa.

---

## 6. Logging

- Log in inglese, stile ibrido testo libero + `chiave=valore`
- Mai dati sensibili (credenziali, path con auth) nei log
- Ogni eccezione inattesa è loggata con contesto completo (`exc_info=True`) o rilanciata, mai in silenzio. Per un errore di dominio con eccezione nominata (un file assente per quel soggetto, un config non valido) basta il messaggio con la causa: la traccia dello stack sarebbe rumore
- Livelli usati coerentemente: INFO (milestone), DEBUG (dettagli verbosi), WARNING (recuperabile), ERROR (richiede attenzione)
- Ogni entry point di pipeline (`src/pipeline/*.py`, tranne `embedding_app.py`: è un server che resta in ascolto, non ha una durata del run) logga la durata del run (`src/utils/logging_setup.py::log_duration`, chiamata da un `finally` che avvolge il corpo di `main()` da quando lo start time è catturato in poi) - così la durata è nota sia sul path di successo sia su un `return` anticipato per errore, non solo quando il run completa pulito (vedi `docs/debugging/debug_25_08_26.md`)

---

## 7. Documentazione

- Aggiornare `docs/` ad ogni cambio di interfaccia, config o workflow — comprese le rimozioni (una doc su qualcosa che non esiste più è peggio di nessuna doc)
- Tenere separati: come si usa (utente), come è strutturato (architettura), perché è fatto così (dettagli implementativi/algoritmici)

---

## 8. Debug report

- Un file per sessione di debug (`docs/debugging/debug_DD_MM_YY.md`)
- Un bug per sezione, con livello di criticità e "lessons learned" obbligatorio (azionabile, non una parafrasi del bug) (`lessons_learned.md`)

---

## 9. Git e Automazione

- **Nessun commit automatico da parte dell'AI** (fonte unica di questa regola — `.claude/CLAUDE.md` vi rimanda): L'assistente non deve mai creare o eseguire commit in modo automatico senza una esplicita richiesta dell'utente. Le modifiche vanno solo apportate ai file.

---

## Riferimenti

- [`.claude/CLAUDE.md`](../.claude/CLAUDE.md) — struttura repo e convenzioni generali NEMESIS
- [`src/utils/subject_ids.py`](../src/utils/subject_ids.py) — esempio attuale di gestione errori conforme al §0 (un sito non registrato solleva, non viene indovinato)
