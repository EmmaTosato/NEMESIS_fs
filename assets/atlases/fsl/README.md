# Atlanti FSL

Atlanti anatomici probabilistici distribuiti con FSL, usati per classificare le lesioni per sede (corticale / sotto-corticale / infratentoriale).

## Contenuto

| Cartella | Atlante | Etichette | File label |
|---|---|---|---|
| `HarvardOxford/` | Harvard-Oxford corticale (`cort`) | 48 | `HarvardOxford-Cortical.xml` |
| `HarvardOxford/` | Harvard-Oxford sotto-corticale (`sub`) | 21 | `HarvardOxford-Subcortical.xml` |
| `Cerebellum/` | Cerebellum MNIfnirt (Diedrichsen) | 28 | `Cerebellum_MNIfnirt.xml` |

Versione `maxprob-thr25`, a 1mm e 2mm: ogni voxel porta l'etichetta più probabile, purché la sua probabilità sia almeno 25%, altrimenti vale 0.

## Fonte

Pacchetto FSL 5.0.7 ospitato da FreeSurfer: `https://ftp.nmr.mgh.harvard.edu/pub/dist/freesurfer/tutorial_packages_centos6/centos6/fsl_507/data/atlases/` (sottocartelle `HarvardOxford/` e `Cerebellum/`, XML nella cartella `atlases/`). File copiati senza modifiche.

## Come leggerli

- **Indici**: il valore voxel nel NIfTI è `index` dell'XML + 1 (0 = nessuna etichetta). Gli indici si leggono sempre dall'XML, mai per offset (`.claude/lessons_learned.md` #11).
- **Orientamento**: gli atlanti sono LAS (x decrescente nell'array), i template in `assets/templates/` sono RAS. Stessa shape e stesso spazio mondo (MNI152 di FSL), ma l'array è speculare sull'asse x: il confronto con i template va fatto tramite l'affine, mai per posizione nell'array.
- **Etichette non anatomiche**: l'atlante sotto-corticale contiene anche `Cerebral White Matter`, `Cerebral Cortex` e `Lateral Ventricle` per emisfero, e `Brain-Stem` (un solo slot, non bilaterale).

## Riferimenti

- Harvard-Oxford: Makris et al. 2006 (*Schizophr Res*), Frazier et al. 2005 (*Am J Psychiatry*), Desikan et al. 2006 (*NeuroImage*), Goldstein et al. 2007 (*Biol Psychiatry*).
- Cerebellum: Diedrichsen et al. 2009, "A probabilistic MR atlas of the human cerebellum" (*NeuroImage*).

## Licenza

Gli XML e i NIfTI non dichiarano una licenza. Gli atlanti sono distribuiti con FSL, che ha una propria licenza (`https://fsl.fmrib.ox.ac.uk/fsl/docs/#/license`): da verificare prima di ridistribuire questi file fuori dal progetto.
