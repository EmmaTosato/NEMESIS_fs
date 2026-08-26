# Allineamento checkout (main unico, server + locale)

*Ultimo aggiornamento: 2026-08-26*

Non esistono più due branch (`server-pnc` è stato eliminato) — un solo `main`, lavorato **contemporaneamente da due checkout**: il server (cluster) e il PC locale. Nessuna eccezione di file/cartelle da gestire: è lo stesso identico branch, quindi la sincronizzazione è pura questione di `git pull`/`git push` tenuti allineati tra i due checkout.

## Regola Aurea

- **Prima di iniziare a lavorare** (su uno qualsiasi dei due lati): `git pull` — potresti non avere l'ultima modifica fatta dall'altro lato.
- **Appena finito di lavorare** (anche a metà, prima di spostarti sull'altro lato): `git push` — non lasciare commit locali non pushati mentre lavori dall'altra macchina, altrimenti l'altro lato non li vede e rischia di divergere.

In pratica: ogni volta che si passa da un lato all'altro (server ↔ locale), **pull in entrata, push in uscita**. Se te ne dimentichi e provi a pushare con l'altro lato avanti, `git push` fallisce (non fast-forward) — non forzare, vedi sotto.

## Se `git pull` fallisce (non fast-forward / conflitti)

Significa che entrambi i lati hanno commit non condivisi.

```bash
git status --short          # lavoro non committato? mettilo da parte prima
git stash push -m "wip"     # se serve
git fetch origin
git rebase origin/main       # riallinea i tuoi commit sopra quelli remoti
git stash pop                # se avevi stashato
```

Se il rebase produce conflitti, risolverli manualmente file per file — non usare `git rebase --skip` per buttare via modifiche senza guardarle.

## Se hai lavorato senza pull/push per un po' (entrambi i lati con commit propri)

```bash
git fetch origin
git log --oneline main..origin/main    # cosa c'è di nuovo sull'altro lato
git log --oneline origin/main..main    # cosa hai tu che l'altro lato non ha
git rebase origin/main
git push origin main
```

## Nota

Niente più eccezioni "regola verificabile" (quelle esistevano solo per la divergenza strutturale tra due branch diversi). `data/`, `results/`, `logs/`, `summaries/` restano comunque gitignored come sempre (non sono nemmeno tracciati, quindi non c'entrano con l'allineamento tra checkout) — vedi `.gitignore`.
