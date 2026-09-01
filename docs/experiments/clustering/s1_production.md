# Diario Esperimenti

**Pipeline:** Clustering (Produzione)

**Dati:** Low dimensional embedding o dati raw

**Sessione:** s1 

**Tipo di dati**: Lesion Data (matrice voxel-wise volumetrica)

**Origine**: data/derived/lesion_matrix

**Note**
- Parametri scelti a valle del tuning ([`s1_tuning.md`](s1_tuning.md)).
- Vedi data_sessions.md per specifica sulle sessioni

---

_Nessuna run di produzione ancora loggata — il k finale per s1.1 non è ancora stato scelto (6 opzioni già lanciate in `results/lesion/clustering/production/*/umap/01-09_s1.1_*`, decisione utente ancora aperta, vedi `.claude/stato_progetto.md`). Struttura entry da usare una volta deciso:_

```
## DD-MM-YYYY — sX.X

#### <titolo>

- **Input:**
    - sX.X
    - Embedding: <metodo, parametri>
    - Path: <tag embedding usato come input_path>
    - Dati originali: data/derived/lesion_matrix/<...>
    - N soggetti
- **Metodi:** <metodo scelto>
- **Obiettivo:**
    - ...

**Risultati**

<tabella o descrizione>

**Decisioni**

- ...
```
