Date: 07/07/2026
People: Sebastiano

> Data driven project 

# Dataset Lesioni
Cartella  EBRAIN: /data/corbetta/Clinical_connectome

- /data/corbetta/Clinical_connectome/UNIPD --> Padova
- /data/corbetta/Clinical_connectome/UKFLR —> Friburgo
- /data/corbetta/Clinical_connectome/UKE —> Amburgo
- /data/corbetta/Clinical_connectome/FIDIS —> Santiago
- /data/corbetta/Clinical_connectome/UCL —> Londra 

Cartella Nemesis: /data/corbetta/<>/NEMESIS —-> Padova

#### Datasets:
1. Washu  (n = 200)
2. PASPORT (n = 100)
3. PSP (n = circa 200)
4. stroke_UKLFR (n = 700)
5. Manca un dataset grosso, clinico di Amburgo (n = 500) —> arriverà
6. Potremmo chiedere accesso di 4100 lesioni di UCL  (?)
7. Santiago 
  
200 + 100 + 200 + 700 + 500+ 4100  = 5800
  
#### Struttura interna 
Per ogni dataset, e singolo soggetto 
- anat (sequenze in nativo): 
	- lesioni segmentate in T1
- derivatives (lesioni già in MNI, nel templato, 1mm / 2mm ?)
	- manual_masks/<\soggetto>/anat/<>/nii.gz


#### Info
- Prefix:
	- HC = healthy
	- ST =stroke
	- PD = Parkison Disease
- particpants.tsv —> informazioni demografiche e cliniche (tabulari).
- L’idea è che più aumenti il numero, più la distribuzione delle lesioni copre la distribuzione empirica dellos stroke.


# Mappe di Lesioni
- Lesioni
- Mappe (Thiebaut)
  

# SDC
- Foulon (Thiebaut) —> whole brain SDC (disconessione a livello globale)
- BCBToolKIt impelmetnano questa computazione
- Goals
	- Disconessione in funzione delle lesioni 
	- E anche come la lesione e SDC overlappano con sottocorticali etc (atlas) —> mi valuti questa regione in funzione degli atlas
- Probabolità da 0 a 1 in ogni voxel, prob che la stramline sia disconessa
- Vedi Mail
- L’outout del toolbox, per ogni soggetto:
	- statistiche lesioni + disconnectoma
	- disconectome parcelizzato per un tot di altas
	- lesione parcelizzato per un tot di altas
	- disconectome non parcellizzato (volumetrico più grezzo)


# Low dimensional embedding
- ad esempio UMAP
- Territori vascolari diversi (le lesioni rispecchiano la struttura vascolare)
- lesioni in cluster diversi si ritrovano nello stesso cluster quando faccio sdc perchè magari appartengono allo stresso strameline disconesso
- la dimensionalità delle lesioni è estrmamente più alta, mentre le sdc trova le strade in comune, quindi mi si abbasa la dimensionalità

# Interpetazione clinica
- Media dei disconnettomi all’interno del cluster
- Interpretazione clinica 
	- tsv
	- NHSS (score totale) che posso plottare
	- plottare diversi dataset per vedere qual è la copertura devi vari dataset
	- subitem corrispondono ai dei domini ( 9 linguaggio —> cluster sinistrofrontale / 11 neglect / 5a al 6b motorio )
- Colora l’embeeding con queste info


# Task 3
- Feature strutturali e funzionali in arrivo
- In teoria per WU+PD+fri, potremmo avere
	- matrici di connettività funzionale 
	- matrici di connettività strutturale
- Servono coorti che abbiamo sani per fare queste matrici funzionali e struttrali

Clinical_connectome/features/<\dataset>/func, dentro trovi le features


#### Workflow:
- cluster degli SDC
- Posso prendere cluster x (itero per tutti i cluster)
- descrivo la connettività funzionale rispetto ai sani per tutti i soggetti nel cluster
- posso farlo sia per BOLD che diffusione (numeri circa uguali)
- Sarebbe molto power per cluster anatomico (quello che viene fuori dalle lesioni): tutti i pazienti che hanno questa lesione prototipica, hanno questo patter funzionale/ di diffisione = renderebbe le rispsote contestuallizzate, specifiche a quel sottogryppo clinico e neuroanatomico
  
SDC: stima indiretta del danno  
DWI: vado a vedere quello che è rimasto, dato diretto di diffusione

# EEG
(TBD) —> settembre/ottobre


# Hints
- Come confrontare i clustering di diversi embedding
- A livello di spazio fisico nel cervello, capire come il delta (frqueneza EEG) spiega gli effetti di trovati da Siegel 2016
  
# Meeting di fine luglio
- Stroke introduction
- Domanda: feature space —> sullo stroke abbiamo diverse storie non collegate, per avere avere una vissione olistica sugli aspetti anatomico, funzionale, struttuarale e fisologico, dobbiamo enttere insieme questi segnalo
	- dataset multimodali
- Ipotesi
	- H0: come si overlappano le modalità
- Idee  
	- low dimensional embedding 
	- punterei sui numeri
	- punterei sul multimodale
- Task1 e Task2
- Abozzare i risultati del task 3 (?)
- Peoggetto apripista