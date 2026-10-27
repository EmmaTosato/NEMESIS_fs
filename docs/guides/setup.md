# Setup ambiente

## Ambiente conda: `nemesis`

Il progetto usa un ambiente conda dedicato chiamato **`nemesis`**, definito in [`environment.yml`](../../environment.yml) alla radice del repo. L'elenco dei pacchetti sta solo lì: non è ripetuto in nessun documento.

`environment.yml` non fissa le versioni: due macchine possono avere versioni diverse dello stesso pacchetto.

### Creare l'ambiente

```bash
conda env create -f environment.yml
```

### Attivare l'ambiente

```bash
conda activate nemesis
```

### Aggiungere un pacchetto

Aggiungere la dipendenza a `environment.yml`: nella sezione `dependencies` per i pacchetti installati da conda-forge, nella sezione `pip:` per quelli installati da PyPI. Poi aggiornare l'ambiente:

```bash
conda env update -f environment.yml -n nemesis
```

Senza `--prune`: con quell'opzione conda rimuove ogni pacchetto non elencato nel file, compreso uno installato a mano.

## Ambiente per ADP (`dadapy`)

Il clustering ADP (`"adp"` in `clustering_methods`) richiede il pacchetto `dadapy`, che dipende da `jax` e non è in `environment.yml`. Vive in un ambiente conda separato, `nemesis_fallback`, che serve solo a ADP; tutto il resto del progetto resta in `nemesis`. Le run ADP partono da lì (vedi [`clustering.md`](clustering.md), sezione "ADP"). Quell'ambiente non ha `dash` né `hdbscan`: `embedding_app`, gli altri metodi di clustering e i loro test non vi girano.

Versioni dei pacchetti che contano: Python 3.11, `dadapy` 0.3.4, `jax` e `jaxlib` 0.4.30, `numpy` 1.26.4, `scikit-learn` 1.9.1. Nessun file del repo lo crea. Su una macchina nuova si parte da un ambiente Python 3.11 con i pacchetti scientifici di base (`numpy`, `scipy`, `pandas`, `scikit-learn`, `matplotlib`, `seaborn`) e si installa `dadapy` da PyPI:

```bash
conda create -n nemesis_fallback python=3.11 numpy=1.26 scipy pandas scikit-learn matplotlib seaborn
conda activate nemesis_fallback
pip install dadapy==0.3.4
```

Questi comandi sono ricostruiti dall'elenco dei pacchetti dell'ambiente in uso, non provati su una macchina pulita.
