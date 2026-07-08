# Setup ambiente

## Ambiente conda: `nemesis`

Il progetto usa un ambiente conda dedicato chiamato **`nemesis`**, definito in [`environment.yml`](../environment.yml) alla radice del repo.

Pacchetti principali: `numpy`, `scipy`, `pandas`, `scikit-learn`, `umap-learn`, `matplotlib`, `seaborn`, `networkx`, `jupyterlab`, `nibabel`, `nilearn`.

### Creare l'ambiente

```bash
conda env create -f environment.yml
```

### Attivare l'ambiente

```bash
conda activate nemesis
```

### Aggiungere un pacchetto

Aggiungere la dipendenza a `environment.yml` (sezione `dependencies` per pacchetti conda-forge, sezione `pip:` per pacchetti disponibili solo su PyPI), poi aggiornare l'ambiente:

```bash
conda env update -f environment.yml -n nemesis --prune
```

## Organizzazione del codice

- **`src/`** — codice di progetto (pipeline SDC, embedding, clustering, ecc.)
- **`scripts/`** — script accessori/one-off (es. download e organizzazione dataset, utility di setup)
