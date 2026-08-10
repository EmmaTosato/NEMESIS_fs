# Guida al Clustering (Raggruppamento)

Questa guida illustra l'uso dello script `clustering.py`. L'obiettivo è analizzare una matrice matematica di pazienti e raggrupparli automaticamente in "cluster" (gruppi o sottotipi). I pazienti appartenenti allo stesso cluster avranno lesioni cerebrali simili.

**Script**: `src/pipeline/clustering.py`
**Configurazione**: `config/pipelines/clustering.json`

## Esecuzione (Locale vs Server/SLURM)

**1. Esecuzione sul Server (con SLURM)**
Sul server, lancia lo script inviandolo alla coda tramite SLURM (così non si interrompe se chiudi la connessione). Trovi lo script in `jobs/`:
```bash
sbatch jobs/run_clustering.sh
```

**2. Esecuzione in Locale (senza SLURM)**
Dal tuo PC locale, dopo aver attivato l'ambiente `nemesis`, lancia la pipeline direttamente da terminale:
```bash
python -m src.pipeline.clustering --config config/pipelines/clustering.json
```
## Il concetto: cosa significa "Clustering"?

Mentre il *Matrix Building* ci dice l'estensione del danno e la *Dim Reduction* semplifica le informazioni estraendo i pattern principali, il Clustering fa un passo interpretativo. Gli algoritmi analizzano le "distanze matematiche" tra i pazienti. Pazienti "vicini" tra loro vengono racchiusi in un cerchio invisibile ed etichettati, ad esempio, come "Pazienti di Tipo 1".

Puoi lanciare il clustering direttamente sulla matrice parcellizzata grezza (ad esempio su 372 colonne, anche se gli algoritmi faranno molta fatica), o, molto meglio, puoi lanciarlo sulla matrice "compressa" generata dopo un passaggio di *Dim Reduction* (sulle famose 2 o 3 componenti principali).

---

## Le Due Modalità di Funzionamento: Produzione e Fine-Tuning

Come `dim_reduction.py`, anche `clustering.py` ha due modalità, controllate dal parametro `"fine_tuning"`.

### 1. Modalità Fine-Tuning (`"fine_tuning": true`)
Il clustering non ha un "punteggio oggettivo" come la trustworthiness della riduzione dimensionale (non c'è una verità di base con cui confrontarsi), quindi gli indici usati qui sono tutti interni: guardano solo `(dati, etichette di cluster)` e misurano quanto i gruppi trovati sono compatti/separati tra loro — mai un confronto tra metodi diversi, solo tra valori diversi dello stesso iperparametro per lo stesso metodo.

Attivando questa modalità, per ogni metodo in `clustering_methods` lo script prova tutti i valori dichiarati nel `tuning_grid` di quel metodo (`config/registry/params_clustering.json`) e calcola, per ciascuno: **silhouette score**, **Calinski-Harabasz**, **Davies-Bouldin** (generici, uguali per tutti e 5 i metodi). K-Means guadagna anche una colonna `inertia` (criterio del gomito), GMM guadagna `bic`/`aic` (criteri basati sulla verosimiglianza). Due metodi ricevono in più un grafico diagnostico "a sé stante", indipendente dalla griglia provata: **Agglomerative** un dendrogramma, **Spectral** un grafico dell'eigengap — **HDBSCAN** non ne ha uno: a differenza di DBSCAN non c'è un singolo `eps` da leggere a occhio su un grafico, `min_cluster_size` si giudica direttamente dalle colonne `noise_fraction`/silhouette già sweepate. Nessuna selezione automatica — spetta a te leggere `tuning_results.csv`/i grafici e scegliere il valore a mano.

`tuning_grid` dichiara oggi **un solo parametro per metodo** (`n_clusters` per KMeans/Agglomerative/Spectral, `n_components` per GMM, `min_cluster_size` per HDBSCAN), quindi il grafico è sempre una curva (una per metrica) — con due parametri diventerebbe una heatmap (due assi, una per metrica), con più di due `tuning_results.csv` viene comunque scritto con tutte le combinazioni ma non viene generato nessun grafico (solo un warning in log).

#### Consensus/stability clustering (opzionale, solo kmeans/gmm/spectral)

Oltre ai 3 indici generici, per `kmeans`/`gmm`/`spectral` puoi attivare due colonne aggiuntive che misurano **quanto è stabile** un certo `k`, non solo quanto è "buono" su un singolo run (vedi `docs/knowledge/clustering.md` per la spiegazione completa e i riferimenti in letteratura). Sono disattivate di default — per attivarle, aggiungi un blocco `"consensus"` dentro l'entry del metodo in `config/registry/params_clustering.json`:

```json
"kmeans": {
  "params": { "n_clusters": 6, "random_state": 0, "n_init": "auto" },
  "tuning_grid": { "n_clusters": [2, 3, 4, 5, 6, 8, 10] },
  "consensus": {
    "rsc": { "n_repeats": 200 },
    "monti": { "n_repeats": 200, "subsample_fraction": 0.8 }
  }
}
```

- `"rsc"` (opzionale): ripete il metodo `n_repeats` volte sugli stessi identici dati, cambiando solo il seed casuale — misura quanto l'assegnazione dipende dal caso dell'inizializzazione. Aggiunge la colonna `rsc_eigengap` (più alto = più stabile).
- `"monti"` (opzionale): ripete il metodo `n_repeats` volte su un sottocampione casuale di soggetti (`subsample_fraction`, es. `0.8` = 80%) — misura quanto l'assegnazione dipende da chi c'è nel campione. Aggiunge la colonna `monti_stability` (più alto = più stabile).

Puoi attivarne uno solo o entrambi. Quando presenti, `tuning_plot.png` include anche queste colonne, e nella stessa cartella trovi un file separato `consensus_suggestions.md` con il `k` suggerito da ciascun metodo (es. "RSC suggests n_clusters=4 (...)") — un'informazione in più da guardare insieme alle altre, mai scritta dentro `config.md` (quello resta sempre uno snapshot statico di come hai lanciato la pipeline) né una scelta automatica applicata al posto tuo.

### 2. Modalità Produzione (`"fine_tuning": false`)
Una volta scelti i parametri (es. `n_clusters`) e salvati in `config/registry/params_clustering.json`, lanci lo script in questa modalità: produce il clustering finale, come descritto sopra.

---

## Dettaglio dei Parametri JSON

Spiegazione delle impostazioni in `config/pipelines/clustering.json`:

- **`project`**: `(Stringa)` Il nome del tuo progetto, es. `"clinical_connectome"`.
- **`input_path`**: `(Stringa)` Il percorso della matrice su cui vuoi calcolare i gruppi. DEVE essere una cartella esistente. Se vuoi clusterizzare i dati grezzi, passa il percorso di `data/derived/lesion_matrix/...`. Se vuoi clusterizzare i dati compressi, passa il percorso di `results/lesion/dim_reduction/...`.
- **`clustering_methods`**: `(Lista di Stringhe)` Questo è un punto chiave. Lo script ti permette di scatenare un intero battaglione di algoritmi diversi nello stesso momento per poterli confrontare. Inserisci i metodi che ti interessano. Supportiamo:
  - `"kmeans"`: Il più famoso. Divide lo spazio a spicchi geometrici. Tende a fare gruppi della stessa dimensione sferica.
  - `"agglomerative"`: Crea "famiglie" unendo i pazienti più vicini a cascata. Ottimo per strutture complesse.
  - `"gmm"` (Gaussian Mixture): Immagina i cluster come nuvole ovoidali con una densità che sfuma al centro.
  - `"hdbscan"`: Algoritmo basato sulla densità. Cerca mucchi fitti di pazienti, a densità variabile (non serve fissare una soglia di distanza globale come nel vecchio DBSCAN). È l'unico algoritmo in grado di trovare "Rumore" (Pazienti isolati e inclassificabili, assegnati all'etichetta speciale `-1`).
  - `"spectral"`: Ottimo se i pazienti formano forme strane intrecciate.
- **`params_file`**: `(Stringa)` Il file in cui sono stivati i settaggi intimi dei vari algoritmi (`"config/registry/params_clustering.json"`). 
- **`output_root`**: `(Stringa)` Dove verranno generate le cartelle coi pazienti divisi (`"results/lesion/clustering"` — il primo segmento dopo `results/` indica la modalità dato, `lesion`/`fc`/`sdc`).
- **`session_name`**: `(Stringa)` Come vuoi chiamare l'esecuzione (es. `"test_gruppi_1"`).
- **`overwrite`**: `(Booleano)` A `true` permette di rimpiazzare vecchi test che avevano lo stesso nome.
- **`fine_tuning`**: `(Booleano)` Attiva (`true`) o disattiva (`false`) la modalità di ricerca dei parametri descritta sopra.
- **`run_notes`**: `(Stringa)` Qualsiasi appunto libero (es. "Raggruppo la matrice K-Means a 4 componenti").

### Impostare il numero di Cluster nel file Params
Per quasi tutti gli algoritmi (come KMeans), devi sapere in anticipo quanti gruppi vuoi formare. Per dirglielo, non devi toccare la configurazione vista sopra, ma devi aprire il file logico: `"config/registry/params_clustering.json"`.
Lì dentro, ad esempio sotto la voce "kmeans", c'è la variabile `"n_clusters": 4`. Puoi cambiare quel `4` nel numero desiderato prima di avviare il comando.

---

## Output e Grafici di Confronto

Eseguendo lo script con, supponiamo, due metodi (`["kmeans", "hdbscan"]`), succederà questo:

1. **Creazione Cartelle Singole**: In `results/lesion/clustering/` verranno create le sottocartelle `kmeans/` e `hdbscan/`. All'interno, troverai `matrix.npy` (che in realtà è solo una copia identica della tua matrice di partenza) ma, soprattutto, nel file **`metadata.csv`** verrà aggiunta una magica colonna `"cluster_label"` accanto a ogni paziente. Se per un paziente c'è scritto `2`, significa che è finito nel Gruppo 2.
2. **Grafico Base**: Sempre nella singola cartella, lo script abbozzerà un piccolo grafico immagine `cluster_plot.png` bidimensionale colorato con i gruppi. (*Nota Bene: disegna solo le primissime due colonne della matrice. Se stai clusterizzando dati non compressi, è utile solo come occhiata generica, non come rappresentazione affidabile.*) Nella stessa cartella trovi anche `cluster_plot_interactive.html`, la versione interattiva apribile in un browser: passando sopra un punto vedi `subject_id`/`dataset`/gruppo di quel paziente, e un menu a tendina in alto ti fa passare dalla colorazione per gruppo a quella per dataset — utile per capire se un confine tra cluster riflette una vera struttura clinica o solo un effetto sito/dataset.
3. **Grafico Silhouette per Paziente**: `silhouette_plot.png`, sempre nella stessa cartella — il classico grafico a due pannelli: a sinistra una "banda" orizzontale per ogni gruppo, larga quanto il coefficiente di silhouette di ciascun paziente di quel gruppo (più la banda è larga e uniforme, meglio quel gruppo è separato dagli altri; se scende sotto lo zero, quei pazienti sono in realtà più vicini a un gruppo diverso dal proprio), con una linea tratteggiata sulla media — la stessa media riportata come "silhouette" nel tuning. A destra lo stesso scatter di `cluster_plot.png`, per confronto visivo immediato. Calcolato sulla matrice intera usata per clusterizzare (non solo le 2 colonne del grafico base), quindi affidabile anche quando `cluster_plot.png` non lo è. Se il risultato è degenere (es. un solo gruppo), il file non viene creato e nel log compare un warning invece di un errore.
4. **Grafico di Comparazione**: Lo script è programmato per farti un favore enorme. Se gli dai più di un metodo da testare, creerà una cartella speciale chiamata `comparison/`. Lì dentro piazzerà un'immagine `cluster_plot_comparison.png` mettendoti affiancati i grafici di K-Means e di HDBSCAN con identica visuale geografica. Così a colpo d'occhio capirai quale dei due algoritmi sta dividendo il "blob" di pazienti nella maniera più sensata per la ricerca clinica.

**Se invece eri in Fine-Tuning** (`"fine_tuning": true`): niente `matrix.npy`/`cluster_plot.png` — per ogni metodo trovi `results/lesion/clustering/<metodo>/tuning/<GIORNO-MESE>_<session_name>/` con `tuning_results.csv` (una riga per combinazione provata, con le metriche descritte sopra) e `tuning_plot.png` (un sottografico per metrica). Per Agglomerative/Spectral trovi in più, nella stessa cartella, il grafico diagnostico specifico del metodo (`dendrogram.png`/`eigengap_plot.png`) — HDBSCAN non ne ha uno (vedi sopra).

**I file `runs.csv`/`runs_tuning.csv`**: esattamente come per `dim_reduction.py` (vedi quella guida), ogni cartella di metodo accumula un diario di bordo interrogabile, mai sovrascritto — ma in **due file separati**, non uno: `results/lesion/clustering/kmeans/runs.csv` per le esecuzioni di produzione, `runs_tuning.csv` per quelle di fine-tuning (stesse colonne: `session, id, timestamp, params, output, notes`).
