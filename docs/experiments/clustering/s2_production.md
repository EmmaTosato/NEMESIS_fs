# Diario Esperimenti

**Pipeline:** Clustering (Produzione)

**Dati:** Low dimensional embedding o dati raw

**Sessione:** s2

**Tipo di dati**: Structural Disconnection (SDC) Data

**Origine**: data/derived/sdc_matrix

**Note**
- Parametri scelti a valle del tuning ([`s2_tuning.md`](s2_tuning.md)).
- Vedi data_sessions.md per specifica sulle sessioni

---

_Nessuna run di produzione ancora loggata — s2.1 è ferma al tuning (vedi `s2_tuning.md`), in attesa di estendere l'analisi a `nc3` e di decidere la config di produzione. Struttura entry da usare una volta deciso:_

```
## DD-MM-YYYY — sX.X

### <titolo>

##### Input
- sX.X
- Embedding: <metodo, parametri>
- Path Embedding: <cartella `input_path` in `dim_reduction/production/`, es. `31-08_s2.1_m_euclidean_nc2` — NON la cartella di output di clustering stesso>
- Dati originali: data/derived/sdc_matrix/<...>
- N soggetti
##### Metodi
<metodo scelto>

##### Obiettivo
- ...

##### Risultati

<tabella o descrizione>

##### Decisioni

- ...
```