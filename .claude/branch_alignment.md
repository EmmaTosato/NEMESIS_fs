# Allineamento Branch (main vs server-pnc)

*Ultimo aggiornamento: 2026-08-21*

Sincronizzazione tra `main` (sviluppo) e `server-pnc` (esecuzione cluster).

## Regola Aurea
- **Prima di lavorare su `server-pnc`**: allinealo da `main` (cartelle sotto — sostituzione piena o additiva a seconda della cartella, mai un merge/rebase dell'intero branch).
- **Dopo aver lavorato su `server-pnc`**: se il risultato è codice/config/doc reale (non solo dati/log del run), portalo subito su `main` con la procedura sotto — non lasciarlo accumulare solo qui. Eccezione: le voci in "Eccezioni" restano intenzionalmente divergenti, mai sincronizzarle.

## Cartelle — sostituzione piena (main è source of truth)
`assets/`, `config/` (eccetto retrieval_local/server.json e file_patterns_local/server.json, vedi Eccezioni), `docs/`, `knowledge/`, `scripts/`, `src/`, `tests/`, `.claude/`, `notebooks/`

## Cartelle — additive (si aggiunge il contenuto di main, non si cancella nulla di esclusivo di server-pnc)
- `management/` — note riunioni
- `summaries/` — referti `.md` per-run
- `jobs/` — `server-pnc` ha script SLURM (es. `run_dim_reduction_clustering.sh`) senza equivalente su `main`, che si è ristretto man mano che l'esecuzione locale è diventata il default lì

Prima di una sostituzione piena su una cartella non ancora verificata, controllare che non abbia contenuto esclusivo:
```
diff <(git ls-tree -r --name-only HEAD -- <cartella>/ | sort) <(git ls-tree -r --name-only main -- <cartella>/ | sort)
```
righe `<` = file solo di `server-pnc` → fermarsi e valutare prima di sovrascrivere.

## Fuori scope (mai allineate tra i branch)
- `data/`, `results/` — mai tracciati in git (`.gitignore`), locali per design
- `logs/` — tracciato in git ma mai sincronizzato tra branch: artefatti per-run, restano dove sono stati generati
- `TODO.md` — file singolo, lista di lavoro viva indipendente sui due lati; si sincronizzano solo voci puntuali quando serve

## Eccezioni (divergenza voluta, mai sincronizzare)
- `config/pipelines/retrieval_local.json`/`retrieval_server.json`
- `config/registry/file_patterns_local.json`/`file_patterns_server.json`

Non sono config architetturali ma la richiesta di retrieval *corrente* per quell'ambiente (quali dataset scaricare adesso) — normale che divergano.

## Procedura: portare lavoro da server-pnc a main
1. `git checkout main && git pull --ff-only origin main` — se fallisce, non forzare: c'è lavoro nuovo su `origin/main`, va guardato prima (fetch + rebase).
2. `git worktree add /tmp/main-work main` (non tocca il working tree di `server-pnc`).
3. Nel worktree: `git cherry-pick <hash>` se il commit è pulito; altrimenti copia selettiva dei soli file rilevanti (`git checkout server-pnc -- <file>`) quando il commit mischia roba da escludere (log, config per-ambiente).
4. Commit, `git push origin main`, poi `git worktree remove /tmp/main-work`.

## Procedura: allineare server-pnc a main (per cartella)
- Sostituzione piena: `rm -rf <cartella> && git checkout main -- <cartella> && git add -A -- <cartella>`
- Additiva: `git checkout main -- <cartella> && git add -A -- <cartella>` (senza `rm -rf`)

## Procedura: aggiornare un altro checkout locale (es. un clone sul Mac) dopo un push
Le due procedure sopra aggiornano `main`/`server-pnc` **in un solo repo locale**. Un checkout diverso dello stesso branch (altra macchina, altra cartella) non li vede finché non fa lui stesso un pull da `origin`:
```
git status --short                    # se c'è lavoro non committato:
git stash push -m "wip"
git pull --ff-only origin <branch>    # main o server-pnc
git stash pop
```
Se `pull --ff-only` fallisce (ci sono commit locali non ancora pushati su quel checkout), `git fetch origin && git rebase origin/<branch>` invece di forzare.
