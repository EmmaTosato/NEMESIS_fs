# Allineamento Branch (main vs server-pnc)

*Ultimo aggiornamento: 2026-08-21*

Questo documento traccia la strategia di sincronizzazione tra il branch di sviluppo locale (`main`) e il branch di esecuzione sul cluster (`server-pnc`).

## Regola Aurea
Prima di effettuare qualsiasi operazione manuale o sviluppo sul branch `server-pnc`, ricordati di **tirare giù le ultime modifiche da main** (es. `git pull origin main` oppure un merge controllato) per mantenere l'allineamento. 
Il branch `server-pnc` è attualmente il target di esecuzione: dovrebbe ospitare solo nuovi dati generati e i file di log (`logs/slurm/`), non codice divergente. Le modifiche al codice o ai file di configurazione andrebbero idealmente sempre fatte prima in locale su `main` e poi sincronizzate verso il server.

**Nota dal 21/08**: questa regola era già stata violata due volte prima di essere corretta — il fix `TASK_COUNT` in `jobs/run_compute_sdc.sh` (sessione produzione SDC dell'8/8) e i nuovi pattern in `lessons_learned.md`/`stato_progetto.md` erano nati direttamente su `server-pnc` e mai portati su `main`; `jobs/` inoltre non era mai stato incluso tra le cartelle sincronizzate qui sotto, nonostante contenga script reali (non solo log). Entrambi i gap sono stati chiusi in questa sessione (vedi sotto) — controllare periodicamente che non si riformino, in particolare per `jobs/` dato che gli script vengono spesso modificati/testati direttamente sul cluster per necessità.

## Cartelle Sincronizzate (server-pnc allineato a main)
A partire dal 28 Luglio 2026 (estese il 21 Agosto 2026), le seguenti cartelle su `server-pnc` sono state forzatamente allineate a `main`, che funge da *Source of Truth*:
- `assets/` (inclusi i dataset summaries spostati qui)
- `config/` (sia registry che pipelines; le config SDC sono state integrate nel main e poi spinte sul server)
- `docs/`
- `knowledge/`
- `scripts/`
- `src/` (tutte le nuove logiche di clustering, covariate e distanze)
- `tests/`
- `.claude/` *(dal 21/08)* — narrativa di sessione (`stato_progetto.md`/`stato_progetto_archive.md`/`lessons_learned.md`) verificata prima di ogni allineamento pieno: se `server-pnc` ha accumulato contenuto di sessione non ancora presente su `main`, va prima portato su `main` (append manuale, non sovrascrittura automatica) e solo dopo si esegue l'allineamento pieno — vedi nota sopra.
- `jobs/` *(dal 21/08)* — stessa cautela di `.claude/`: script spesso modificati direttamente sul cluster per necessità operativa (fix urgenti durante un run), vanno controllati per contenuto esclusivo prima di sovrascrivere.
- `notebooks/` *(dal 21/08)* — verificare prima che non ci siano notebook con output/celle uniche di `server-pnc` non ancora rifluiti su `main`.

Due cartelle usano un allineamento **additivo** (si prende il contenuto di `main`, ma non si cancella nulla di esclusivo di `server-pnc`), non una sostituzione piena, perché possono contenere contenuto reale non ancora replicato altrove:
- `management/` (note riunioni — verificare sempre se un file "esclusivo" di `server-pnc` è un vero contenuto originale o solo un duplicato/rinomina di qualcosa già su `main`)
- `summaries/` (esclusivamente stdout e referti in formato `.md`)

## Cartelle esplicitamente FUORI scope (non allineare)
- `data/`, `logs/`, `results/` — dati/log/output locali o di cluster per design, mai versionati/sincronizzati. `results/` è stato allineato a questa policy il 21/08 (`git rm -r --cached`, aggiunto a `.gitignore`) — prima era ancora tracciato su `server-pnc` (243 file) nonostante `main` avesse già smesso (`chore: stop tracking results/ in git`); risolto scegliendo coerenza con `main` invece di tenerlo come eccezione permanente. I file restano su disco su entrambi i lati, solo non più in git.
- `notebooks/` non era qui prima del 21/08 proprio perché i notebook sono spesso modificati in sessioni parallele sullo stesso `.ipynb` — ora inclusa sopra, ma solo dopo aver verificato l'assenza di lavoro esclusivo non recuperabile.
- `TODO.md` — file singolo (non una cartella), lista di lavoro viva aggiornata indipendentemente su entrambi i lati; si sincronizzano solo voci puntuali quando serve, non l'intero file.

## Eccezioni e Divergenze Future (Da Mantenere)
*Nessuna al momento.*

Se in futuro ci saranno differenze che **devono** rimanere tali tra il server e il locale (es. file di test specifici per l'ambiente EBRAIN, variazioni strutturali di `.gitignore`, o configurazioni che su Mac non girerebbero mai), andranno documentate in questa sezione. In tal caso, si eviteranno sovrascritture brutali (come un `git push --force`) a favore di merge chirurgici per salvaguardare queste eccezioni.
