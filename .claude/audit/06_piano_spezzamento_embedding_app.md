# 06 — Piano di spezzamento di `embedding_app.py` (C-022)

**Eseguito il 02-11-26** (12 commit, `9db71c3`..`2ebaa1b`). Le §1-§7 sono il piano come fu scritto il 29-10-26; la §8 dice com'è finito e dove si è deviato. La struttura vera è in `docs/dev/embedding_app.md`.

## 1. Stato attuale

`src/analysis/embedding_app.py`: 5541 righe, 146 definizioni di primo livello, un solo modulo che fa sei lavori diversi.

| Righe | Contenuto | Lavoro |
|---|---|---|
| 1-493 | costanti, colori, `CSS` | stile |
| 493-1085 | `ProductionRun`, `discover_production_runs`, picker, `load_run` | scoperta e caricamento delle run |
| 1085-1450 | `build_embedding_figure`, `graph_content_for` | grafico dell'embedding |
| 1411-2030 | visualizzatori di lesione e disconnessione, mappe per cluster | anatomia |
| 2031-2250 | tabelle, `cluster_description_content_for`, `cluster_composition_content_for` | pannelli descrittivi |
| 2248-2380 | mappe delle componenti PCA | pannello PCA |
| 2381-2880 | qualità del clustering (geometrica, densità, ADP, modello) | pannello qualità |
| 2880-3527 | confronto tra run e tra cluster | sezione «Confronto» (parcheggiata, non montata) |
| 3527-3633 | panoramica di tutti i cluster | pannello panoramica |
| 3633-3869 | dendrogramma e passi di split | scheda dendrogramma |
| 3869-3982 | schede e indice della pagina | navigazione |
| 3982-5541 | `build_app`: 1543 righe di layout e 60 callback in una sola funzione | assemblaggio |

Conseguenza: `build_app` è l'unica funzione che sa dell'intero schermo. I builder dei contenuti (`*_content_for`) sono già funzioni pure e testate; il problema è che stanno tutti nello stesso file e che i callback sono chiusure dentro `build_app`.

## 2. Principi (dal progetto)

- **Livelli** (`code_standards.md` §1): `utils` → `features` → `analysis` → `pipeline`. I moduli nuovi stanno in `analysis`; `src/pipeline/embedding_app.py` resta l'unico punto d'ingresso.
- **Una responsabilità per modulo**, funzioni piccole, nessuno stato globale: le dipendenze si passano come argomenti.
- **Registry esplicito** (`design_patterns.md`): ogni pannello è una voce di una tabella, non un ramo di `if` dentro `build_app`.
- **Value object immutabile**: lo stato condiviso dei callback (run scoperte, cache) diventa un `@dataclass(frozen=True)` costruito una volta, non variabili catturate dalla chiusura.
- **Niente shim di compatibilità** (§2): si aggiornano gli importatori (una pipeline e i test), non si lascia un `embedding_app.py` che ri-esporta.
- **Niente codice morto**, con l'unica eccezione dichiarata della sezione «Confronto».

## 3. Struttura proposta

Un pacchetto `src/analysis/embedding_app/` al posto del file.

```
embedding_app/
  runs.py            ProductionRun, discover_production_runs, picker, load_run          (493-1085)
  style.py           CSS, palette, costanti di layout                                    (160-493)
  embedding_view.py  build_embedding_figure, graph_content_for                           (1085-1450)
  anatomy.py         visualizzatori, mappe per cluster, cache delle viste                (1411-2030)
  context.py         AppContext (frozen): run, cache, store; una factory
  panels/
    __init__.py      PANELS: tabella nome -> (layout, register_callbacks)
    description.py   cluster description + composition                                  (2031-2250)
    pca_maps.py      mappe delle componenti                                              (2248-2380)
    quality.py       qualità geometrica, densità, ADP, modello                           (2381-2880)
    overview.py      panoramica dei cluster                                              (3527-3633)
    dendrogram.py    scheda dendrogramma                                                 (3633-3869)
    comparison.py    «Confronto» (non montato, testato)                                  (2880-3527)
  tabs.py            schede e indice                                                     (3869-3982)
  app.py             build_app: costruisce AppContext, legge PANELS, assembla
```

Ogni modulo di `panels/` espone due funzioni con la stessa firma:

- `layout(ctx: AppContext) -> html.Div`: i componenti del pannello.
- `register_callbacks(app: Dash, ctx: AppContext) -> None`: i suoi callback.

`build_app` diventa: crea `AppContext`, assembla il layout dai pannelli attivi (la tabella `PANELS` dice quali sono montati e in quale scheda), chiama `register_callbacks` di ciascuno. La sezione «Confronto» sta in `PANELS` con un flag di montaggio spento, quindi i suoi builder restano in `src/` e testati senza essere montati.

## 4. Fasi (ognuna lascia la suite verde)

0. **Rete di sicurezza.** Prima di toccare niente: suite completa; uno snapshot degli `id` dei componenti e della mappa dei callback di `build_app` (input/output di ciascuno); uno screenshot headless della pagina con una run di esempio (regola del progetto: le geometrie del layout si verificano con un browser vero).
1. **Moduli senza dipendenze dall'app**: `style.py`, `runs.py`, `embedding_view.py`. Solo spostamenti di funzioni pure; i test cambiano solo gli import.
2. **Builder dei pannelli**: `anatomy.py` e i moduli di `panels/` con le sole funzioni `*_content_for` e i loro helper. Ancora nessun cambio ai callback.
3. **`AppContext`**: le cache `_cached_*` (oggi chiusure dentro `build_app`) diventano campi/metodi di un oggetto costruito una volta.
4. **Callback per pannello**: i 60 callback si spostano nei `register_callbacks` dei pannelli, uno per volta, confrontando ogni volta lo snapshot della fase 0.
5. **`app.py` e `PANELS`**: `build_app` si riduce all'assemblaggio. Aggiornamento di `src/pipeline/embedding_app.py` e dei test (`monkeypatch.setattr(embedding_app, ...)` va puntato al modulo nuovo).
6. **Documentazione**: `docs/dev/models.md` (sezione dell'app), `docs/guides/embedding_app.md` (nessun cambio d'uso), `.claude/CLAUDE.md` (elenco), `docs/dev/pipeline_flow.md` se cita il file.

## 5. Rischi e come si controllano

| Rischio | Controllo |
|---|---|
| Un `id` di componente cambia o sparisce, un callback perde un input | Snapshot di `id` e callback prima/dopo, confronto automatico a ogni fase |
| I test fanno `monkeypatch` su nomi del vecchio modulo | Si aggiornano per percorso; nessuno shim di ri-esportazione |
| Import circolari tra pannelli e `AppContext` | `context.py` non importa i pannelli; i pannelli importano `context.py` |
| Cache condivise tra callback diversi | Un solo `AppContext` costruito in `build_app`, passato esplicitamente |
| Regressione visiva del layout | Screenshot headless prima/dopo, come richiesto dalle regole del layout Dash |
| Sovrapposizione col lavoro non committato dell'utente su `embedding_app.py` | Iniziare solo dopo che quel lavoro è committato; nessun file toccato mentre il working tree ha modifiche su di lui |

## 6. Definizione di «fatto»

- Nessun modulo sopra le ~800 righe; nessuna funzione sopra le ~150 (obiettivo del §2: «idealmente <30», `build_app` oggi 1543).
- `pytest tests/` verde con lo stesso numero di test (più quelli aggiunti per `PANELS` e `AppContext`).
- Snapshot di `id` e callback identico a quello della fase 0.
- Pagina identica a quella dello screenshot di partenza.
- Docs aggiornate e nessun riferimento al vecchio `src/analysis/embedding_app.py`.

## 7. Stima e ordine

Lavoro per una sessione dedicata, in worktree separato, da iniziare dopo il commit del lavoro in corso sull'app. Le fasi 1-2 sono a basso rischio (spostamenti); la fase 4 è quella che richiede attenzione.

---

## 8. Esito (02-11-26)

12 commit, `9db71c3`..`2ebaa1b`. 18 moduli, 6180 righe, il più grande 652 (`anatomy.py`); `build_app` 1543 → 358. Quale modulo tiene cosa sta in `docs/dev/embedding_app.md`, non qui: questo file è il piano, non la struttura.

### Dove si è deviato dal piano

- **Nessuna tabella `PANELS`** (§3): `build_app` chiama nove `register_*(app, context)` espliciti. Con nove pannelli non interscambiabili — ognuno in una scheda precisa, in un ordine deciso a mano — la tabella aggiunge un'indirezione senza togliere niente di visibile.
- **`build_app` resta in `__init__.py`**, non in un `app.py`: così `from src.analysis.embedding_app import build_app` non cambia per la pipeline né per i test.
- **`panels/cluster_maps.py` e `blocks.py` non erano nel piano.** `blocks.py` (tre helper di presentazione letti da 3-4 pannelli) è dovuto venire *prima* dei pannelli, o ognuno avrebbe importato da `__init__.py`. `cluster_maps.py` è nato da un ciclo di import: tenere i callback delle mappe per cluster in `anatomy.py` creava `anatomy → panels.overview → anatomy`, e il ciclo diceva il vero — quei callback sono uno strato sopra il disegnare una mappa. Lo stesso modulo ha poi riportato `anatomy.py` sotto le 800 righe quando questo ha preso i suoi layout.
- **Ordine diverso dalle fasi §4**: l'`AppContext` (fase 3) è servito *prima* dello spostamento dei callback (fase 4) non per ordine ma perché è ciò che lo ha reso uno spostamento — dopo di esso quasi ogni callback non legge più niente dallo scope di `build_app` tranne quell'oggetto.

### Il criterio §6 non soddisfatto

«Nessuna funzione sopra le ~150 righe»: ne restano tre, `build_app` (358), `panels/cluster_maps.py::register_callbacks` (266) e `anatomy.py::register_callbacks` (188). I callback dentro i due `register_callbacks` sono 12 e 9 e nessuno supera le 30 righe: è la lista delle registrazioni a essere lunga, non il lavoro di una funzione — la stessa forma dell'eccezione già scritta nel §2 di `code_standards.md` per una classe con molti metodi piccoli e coesi. Nel repo le funzioni sopra le 30 righe passano da 211/960 a 225/991, quelle sopra le 200 da 2 a 3: lo split ha abbassato il massimo, non il conteggio. **Criterio ritirato il 03-11-26**: la soglia dell'utente è 800-1000 righe, non ~150, e nessuna funzione del repo la supera — le tre funzioni restano come sono.

Le 358 righe di `build_app`, misurate: docstring 33, controlli (`_picker_field`, i bottoni di colore e di griglia, il blocco `controls-section` dentro il layout) 78, i corpi delle tre schede 104, `_preload_stores` 35, `_update_cluster_picker` 13, le nove chiamate `register_*` 9, il resto assemblaggio.

### La rete, e perché non bastava lo snapshot

Con `suppress_callback_exceptions=True` un callback cablato a un `id` inesistente non spara e non solleva. Lo snapshot del contratto prende un `id` che cambia, non un corpo che si rompe: `coverage` sul file vecchio ha mostrato **22 callback su 44 mai eseguiti da alcun test** (circa 120 righe di logica). I 68 test scritti prima dello spostamento (55 di cablaggio, 10 su `AppContext`, 3 sul contratto) hanno poi intercettato i due errori veri del lavoro, entrambi di nome: `ctx` per il contesto dell'app oscurava `from dash import ctx` (13 test rossi), e il successivo `context` collideva con una variabile locale di un callback del dendrogramma (3 rossi).

Oltre alla suite: sha256 di `/_dash-layout` identico prima/dopo (20694 byte, pannelli nascosti compresi), screenshot headless identico al pixel, e quattro confronti su dati veri aggiunti via via — perché lo screenshot della pagina senza run scelta non mostra nessuno dei pannelli spostati.

Suite finale: **5822 passed, 17 skipped**; 392 test nei file dell'app.
