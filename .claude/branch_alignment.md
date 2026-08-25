# Allineamento Branch (main vs server-pnc)

*Ultimo aggiornamento: 2026-08-22*

Sincronizzazione tra `main` (sviluppo) e `server-pnc` (esecuzione cluster).

## Regola Aurea
- **Prima di lavorare su `server-pnc`**: allinealo da `main` (sostituzione piena delle cartelle sotto).
- **Dopo aver lavorato su `server-pnc`**: se il risultato è codice/config/doc reale (qualunque cosa fuori dalle eccezioni sotto), portalo subito su `main` con la procedura in fondo — non lasciarlo accumulare solo qui.

## Regola verificabile

**Tutto il repository deve essere identico tra `main` e `server-pnc`**, tranne:
- `TODO.md`
- `data/`
- `results/`
- `.gitignore`
- `logs/`
- `summaries/`
- `config/pipelines/retrieval_local.json`/`retrieval_server.json`
- `config/registry/file_patterns_local.json`/`file_patterns_server.json`

Verifica:
```bash
git diff --stat main server-pnc -- \
  ':!TODO.md' ':!data' ':!results' ':!.gitignore' ':!logs' ':!summaries' \
  ':!config/pipelines/retrieval_local.json' ':!config/pipelines/retrieval_server.json' \
  ':!config/registry/file_patterns_local.json' ':!config/registry/file_patterns_server.json'
```
**Vuoto = allineati.** Se non è vuoto, `server-pnc` è indietro rispetto a `main` (o viceversa) — va risolto, non è un'eccezione da aggiungere alla lista.

## Perché proprio queste eccezioni

- **`TODO.md`** — lista di lavoro viva, aggiornata indipendentemente sui due lati.
- **`data/`, `results/`** — mai tracciati in git (`.gitignore`), locali per design.
- **`.gitignore`** — può divergere leggermente per differenze di ambiente.
- **`logs/`, `summaries/`** — artefatti **generativi**: ogni run di pipeline (su un lato o sull'altro) scrive un file nuovo, con timestamp nel nome, solo lì. Non convergeranno mai stabilmente — anche dopo un sync perfetto, il prossimo run su un lato qualsiasi li fa tornare a divergere. Non è un ritardo da chiudere, è strutturale.
- **`config/pipelines/retrieval_local.json`/`retrieval_server.json`, `config/registry/file_patterns_local.json`/`file_patterns_server.json`** — non sono config architetturali, sono la richiesta di retrieval *corrente* per quell'ambiente (quali dataset scaricare adesso) — normale che divergano. *Incidente reale (21/08)*: una di queste è stata sovrascritta da un sync pieno di `config/` trattato come blocco unico, perdendo una modifica locale non ancora committata (recuperata dallo stash) — da qui l'esclusione esplicita.

Ogni altro file/cartella (inclusi `management/`, `jobs/` — non più eccezioni dal 22/08, il loro contenuto esclusivo è stato portato su `main` una volta per tutte) deve essere **byte-per-byte identico**.

## Procedura: portare lavoro da server-pnc a main
1. `git checkout main && git pull --ff-only origin main` — se fallisce, non forzare: c'è lavoro nuovo su `origin/main`, va guardato prima (`git fetch` + `git rebase origin/main`).
2. `git worktree add /tmp/main-work main` (non tocca il working tree di `server-pnc`).
3. Nel worktree: `git cherry-pick <hash>` se il commit è pulito; altrimenti copia selettiva dei soli file rilevanti (`git checkout server-pnc -- <file>`) quando il commit mischia roba da escludere (log, config per-ambiente).
4. Commit, `git push origin main`, poi `git worktree remove /tmp/main-work`.

## Procedura: allineare server-pnc a main
Per ogni cartella nella "Regola verificabile" sopra (tutte a sostituzione piena ora):
```bash
rm -rf <cartella> && git checkout main -- <cartella> && git add -A -- <cartella>
```
Prima di farlo su una cartella non controllata di recente, verifica che non abbia contenuto esclusivo:
```bash
diff <(git ls-tree -r --name-only HEAD -- <cartella>/ | sort) <(git ls-tree -r --name-only main -- <cartella>/ | sort)
```
righe `<` = file solo di `server-pnc` → fermarsi, portarlo su `main` prima di sovrascrivere (procedura sopra), non cancellarlo alla cieca.

## Procedura: aggiornare un altro checkout locale (es. un clone sul Mac) dopo un push
Le due procedure sopra aggiornano `main`/`server-pnc` **in un solo repo locale**. Un checkout diverso dello stesso branch (altra macchina, altra cartella) non li vede finché non fa lui stesso un pull da `origin`:
```bash
git status --short                    # se c'è lavoro non committato:
git stash push -m "wip"
git pull --ff-only origin <branch>    # main o server-pnc
git stash pop
```
Se `pull --ff-only` fallisce (ci sono commit locali non ancora pushati su quel checkout), `git fetch origin && git rebase origin/<branch>` invece di forzare.
