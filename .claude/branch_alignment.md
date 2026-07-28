# Allineamento Branch (main vs server-pnc)

*Ultimo aggiornamento: 2026-07-28*

Questo documento traccia la strategia di sincronizzazione tra il branch di sviluppo locale (`main`) e il branch di esecuzione sul cluster (`server-pnc`).

## Regola Aurea
Prima di effettuare qualsiasi operazione manuale o sviluppo sul branch `server-pnc`, ricordati di **tirare giù le ultime modifiche da main** (es. `git pull origin main` oppure un merge controllato) per mantenere l'allineamento. 
Il branch `server-pnc` è attualmente il target di esecuzione: dovrebbe ospitare solo nuovi dati generati e i file di log (`logs/slurm/`), non codice divergente. Le modifiche al codice o ai file di configurazione andrebbero idealmente sempre fatte prima in locale su `main` e poi sincronizzate verso il server.

## Cartelle Sincronizzate (server-pnc allineato a main)
A partire dal 28 Luglio 2026, le seguenti cartelle su `server-pnc` sono state forzatamente allineate a `main`, che funge da *Source of Truth*:
- `assets/` (inclusi i dataset summaries spostati qui)
- `config/` (sia registry che pipelines; le config SDC sono state integrate nel main e poi spinte sul server)
- `docs/`
- `management/`
- `papers/`
- `scripts/`
- `src/` (tutte le nuove logiche di clustering, covariate e distanze)
- `summaries/` (esclusivamente stdout e referti in formato `.md`)
- `tests/`

## Eccezioni e Divergenze Future (Da Mantenere)
*Nessuna al momento.*

Se in futuro ci saranno differenze che **devono** rimanere tali tra il server e il locale (es. file di test specifici per l'ambiente EBRAIN, variazioni strutturali di `.gitignore`, o configurazioni che su Mac non girerebbero mai), andranno documentate in questa sezione. In tal caso, si eviteranno sovrascritture brutali (come un `git push --force`) a favore di merge chirurgici per salvaguardare queste eccezioni.
