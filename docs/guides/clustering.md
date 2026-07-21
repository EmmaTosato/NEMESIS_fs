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

## Dettaglio dei Parametri JSON

Spiegazione delle impostazioni in `config/pipelines/clustering.json`:

- **`project`**: `(Stringa)` Il nome del tuo progetto, es. `"clinical_connectome"`.
- **`input_path`**: `(Stringa)` Il percorso della matrice su cui vuoi calcolare i gruppi. DEVE essere una cartella esistente. Se vuoi clusterizzare i dati grezzi, passa il percorso di `data/derived/lesion_matrix/...`. Se vuoi clusterizzare i dati compressi, passa il percorso di `results/lesion/dim_reduction/...`.
- **`clustering_methods`**: `(Lista di Stringhe)` Questo è un punto chiave. Lo script ti permette di scatenare un intero battaglione di algoritmi diversi nello stesso momento per poterli confrontare. Inserisci i metodi che ti interessano. Supportiamo:
  - `"kmeans"`: Il più famoso. Divide lo spazio a spicchi geometrici. Tende a fare gruppi della stessa dimensione sferica.
  - `"agglomerative"`: Crea "famiglie" unendo i pazienti più vicini a cascata. Ottimo per strutture complesse.
  - `"gmm"` (Gaussian Mixture): Immagina i cluster come nuvole ovoidali con una densità che sfuma al centro.
  - `"dbscan"`: Algoritmo basato sulla densità. Cerca mucchi fitti di pazienti. È l'unico algoritmo in grado di trovare "Rumore" (Pazienti isolati e inclassificabili, assegnati all'etichetta speciale `-1`).
  - `"spectral"`: Ottimo se i pazienti formano forme strane intrecciate.
- **`params_file`**: `(Stringa)` Il file in cui sono stivati i settaggi intimi dei vari algoritmi (`"config/registry/params_clustering.json"`). 
- **`output_root`**: `(Stringa)` Dove verranno generate le cartelle coi pazienti divisi (`"results/lesion/clustering"` — il primo segmento dopo `results/` indica la modalità dato, `lesion`/`fc`/`sdc`).
- **`session_name`**: `(Stringa)` Come vuoi chiamare l'esecuzione (es. `"test_gruppi_1"`).
- **`overwrite`**: `(Booleano)` A `true` permette di rimpiazzare vecchi test che avevano lo stesso nome.
- **`run_notes`**: `(Stringa)` Qualsiasi appunto libero (es. "Raggruppo la matrice K-Means a 4 componenti").

### Impostare il numero di Cluster nel file Params
Per quasi tutti gli algoritmi (come KMeans), devi sapere in anticipo quanti gruppi vuoi formare. Per dirglielo, non devi toccare la configurazione vista sopra, ma devi aprire il file logico: `"config/registry/params_clustering.json"`.
Lì dentro, ad esempio sotto la voce "kmeans", c'è la variabile `"n_clusters": 4`. Puoi cambiare quel `4` nel numero desiderato prima di avviare il comando.

---

## Output e Grafici di Confronto

Eseguendo lo script con, supponiamo, due metodi (`["kmeans", "dbscan"]`), succederà questo:

1. **Creazione Cartelle Singole**: In `results/lesion/clustering/` verranno create le sottocartelle `kmeans/` e `dbscan/`. All'interno, troverai `matrix.npy` (che in realtà è solo una copia identica della tua matrice di partenza) ma, soprattutto, nel file **`metadata.csv`** verrà aggiunta una magica colonna `"cluster_label"` accanto a ogni paziente. Se per un paziente c'è scritto `2`, significa che è finito nel Gruppo 2.
2. **Grafico Base**: Sempre nella singola cartella, lo script abbozzerà un piccolo grafico immagine `cluster_plot.png` bidimensionale colorato con i gruppi. (*Nota Bene: disegna solo le primissime due colonne della matrice. Se stai clusterizzando dati non compressi, è utile solo come occhiata generica, non come rappresentazione affidabile.*) Nella stessa cartella trovi anche `cluster_plot_interactive.html`, la versione interattiva apribile in un browser: passando sopra un punto vedi `subject_id`/`dataset`/gruppo di quel paziente, e un menu a tendina in alto ti fa passare dalla colorazione per gruppo a quella per dataset — utile per capire se un confine tra cluster riflette una vera struttura clinica o solo un effetto sito/dataset.
3. **Grafico di Comparazione**: Lo script è programmato per farti un favore enorme. Se gli dai più di un metodo da testare, creerà una cartella speciale chiamata `comparison/`. Lì dentro piazzerà un'immagine `cluster_plot_comparison.png` mettendoti affiancati i grafici di K-Means e di DBScan con identica visuale geografica. Così a colpo d'occhio capirai quale dei due algoritmi sta dividendo il "blob" di pazienti nella maniera più sensata per la ricerca clinica.
