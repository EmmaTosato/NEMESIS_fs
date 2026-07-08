# Dataset

## Locazione (EBRAIN)

Cartella principale: `/data/corbetta/Clinical_connectome`

| Sito | Path | Città |
|---|---|---|
| UNIPD | `/data/corbetta/Clinical_connectome/UNIPD` | Padova |
| UKFLR | `/data/corbetta/Clinical_connectome/UKFLR` | Friburgo |
| UKE | `/data/corbetta/Clinical_connectome/UKE` | Amburgo |
| FIDIS | `/data/corbetta/Clinical_connectome/FIDIS` | Santiago |
| UCL | `/data/corbetta/Clinical_connectome/UCL` | Londra |

Cartella specifica NEMESIS: `/data/corbetta/<>/NEMESIS` (Padova).

Feature strutturali/funzionali (soggetti sani, per Task 3): `Clinical_connectome/features/<dataset>/func`.

## Coorti e numerosità

| Dataset | N | Note |
|---|---|---|
| WashU | 200 | |
| PASPORT | 100 | |
| PSP | ~200 | |
| stroke_UKLFR | 700 | |
| Amburgo (clinico) | 500 | dataset grosso, in arrivo |
| UCL | 4100 | accesso da richiedere (?) |
| Santiago | — | |

**Totale target ≈ 5800** (200+100+200+700+500+4100).

L'idea di fondo: più aumenta il numero di soggetti, più la distribuzione delle lesioni copre la distribuzione empirica dello stroke.

## Struttura interna (per dataset, per soggetto)

- `anat` — sequenze in nativo
- lesioni segmentate in T1
- `derivatives` — lesioni già in MNI, nel template (1mm / 2mm)
- `manual_masks/<soggetto>/anat/<>/*.nii.gz`

## Convenzioni

- `HC` = healthy (controllo sano)
- `ST` = stroke
- `participants.tsv` — informazioni demografiche e cliniche (tabulari), incluso NIHSS (score totale e sotto-item per dominio, vedi [tasks.md](tasks.md#interpretazione-clinica))
