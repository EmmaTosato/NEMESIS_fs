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

## Ambiente per ADP (`dadapy`)

Il clustering ADP (`"adp"` in `clustering_methods`) richiede il pacchetto `dadapy`, che dipende da `jax` e non è in `environment.yml`: vive in un ambiente conda separato (oggi `nemesis_fallback`, con `dadapy` 0.3.4). Le run ADP partono da lì (vedi [`guides/clustering.md`](guides/clustering.md), sezione "ADP"); tutto il resto del progetto resta in `nemesis`. Quell'ambiente non ha `dash`, quindi `embedding_app` e i suoi test non vi girano.

## Organizzazione del codice

- **`src/`** — codice di progetto (pipeline SDC, embedding, clustering, ecc.)
- **`scripts/`** — script accessori/one-off (es. download e organizzazione dataset, utility di setup)
