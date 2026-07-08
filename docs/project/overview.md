# NEMESIS — Overview

Progetto data-driven (Prof. Corbetta, con Sebastiano e Antonio) che punta a costruire una **rappresentazione multimodale a bassa dimensionalità dello stroke**: incorporare (embedding) lesioni e disconnettomi, raggrupparli (clustering), e mettere in relazione i cluster con connettività strutturale/funzionale e con gli esiti clinico-comportamentali.

**Ipotesi (H0)**: come si sovrappongono le diverse modalità (anatomica, strutturale, funzionale, fisiologica/EEG) nello spiegare il deficit post-stroke. Sullo stroke esistono oggi diverse "storie" non collegate tra loro (anatomica, funzionale, strutturale, fisiologica): per avere una visione olistica serve mettere insieme questi segnali su dataset multimodali.

Idee guida:
- low dimensional embedding come strumento principale
- puntare sui numeri (scala multi-sito, migliaia di soggetti)
- puntare sul multimodale

Per il razionale scientifico dietro queste scelte, vedi la letteratura in `assets/papers/` (richiamata puntualmente qui e nei documenti di metodo quando rilevante).

## Task

Il progetto è organizzato in 5 task, dettagliati in [tasks.md](tasks.md).

## Dataset

Le fonti dati, i path EBRAIN e la struttura interna dei dataset sono in [datasets.md](datasets.md).

## Fonti

- Note di meeting (grezze, non normative ma fonte primaria): `assets/meetings/Brainstorming.md` (24/06/2026), `assets/meetings/Seba Meeting.md` (07/07/2026)
