Date: 07/07/2026
People: Sebastiano

---

> Data driven project

# STATEMENTS 
## Lesioni
Cartella  EBRAIN: /data/corbetta/Clinical_connectome
- /data/corbetta/Clinical_connectome/UNIPD
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
- anat (sequenze in nativo)
- lesioni segmentate in T1
- derivatives (lesioni già in MNI, nel templato, 1mm / 2mm ?)
- manual_masks/<\soggetto>/anat/<>/nii.gz

#### Info
HC = healthy
ST =stroke

participants.tsv —> informazioni demografiche e cliniche (tabulari).

L’idea è che più aumenti il numero, più la distribuzione delle lesioni copre la distribuzione empirica dello stroke.

## SDC
- Foulon (Thiebaut) —> whole brain SDC (disconessione a livello globale)
- BCBToolKIt implementano questa computazione
- Goals
  - Disconnessione in funzione delle lesioni 
  - E anche come la lesione e SDC overlappano con sottocorticali etc (atlas) —> mi valuti questa regione in funzione degli atlas
- Probabilità da 0 a 1 in ogni voxel, prob che la streamline sia disconessa
- L’output del toolbox, per ogni soggetto:
	  - statistiche lesioni + disconnettoma
	  - disconectome parcellizzato per un tot di altas
	  - lesione parcellizzato per un tot di altas
	  - disconectome non parcellizzato (volumetrico più grezzo)
- SDC: stima indiretta del danno
- DWI: vado a vedere quello che è rimasto, dato diretto di diffusione

## Low dimensional embedding
- ad esempio UMAP
- Territori vascolari diversi (le lesioni rispecchiano la struttura vascolare)
- lesioni in cluster diversi si ritrovano nello stesso cluster quando faccio sdc perchè magari appartengono allo stresso strameline disconesso
- la dimensionalità delle lesioni è estrmamente più alta, mentre le sdc trova le strade in comune, quindi mi si abbasa la dimensionalità

## Interpetazione clinica
- Media dei disconnettomi all’interno del cluster
- Interpretazione clinica 
	  - tsv
	  - NHSS (score totale) che posso plottare


## Feature Funzionali
- Feature strutturali e funzionali in arrivo
- In teoria per WU+PD+fri, potremmo avere
	  - matrici di connettività funzionale 
	  - matrici di connettività strutturale
- Servono coorti che abbiamo sani per fare queste matrici funzionali e struttrali

Clinical_connectome/features/<\dataset>/func, dentro troverai le features


## EEG

(TBD) —> settembre/ottobre


# TO DO
- Recupera Lesioni
- Computa SDC
	- BCBToolKIt
	- Vedi Mail
- Prova ad applicare riduzione di dimensionalità
	- UMAP
- Intepretazione Clinica
	- plottare diversi dataset per vedere qual è la copertura devi vari dataset
	  - subitem corrispondono ai dei domini ( 9 linguaggio —> cluster sinistrofrontale / 11 neglect / 5a al 6b motorio
	- Colora l’embeeding con queste info
- Possibile Workflow
- cluster degli SDC
- Posso prendere cluster x (itero per tutti i cluster)
- descrivo la connettività funzionale rispetto ai sani per tutti i soggetti nel cluster
- posso farlo sia per BOLD che diffusione (numeri circa uguali)
- Sarebbe molto power per cluster anatomico (quello che viene fuori dalle lesioni): tutti i pazienti che hanno questa lesione prototipica, hanno questo patter funzionale/ di diffisione = renderebbe le rispsote contestuallizzate, specifiche a quel sottogryppo clinico e neuroanatomico
- Cerca ome confrontare i clustering di diversi embedding
- A livello di spazio fisico nel cervello, capire come il delta (frqueneza EEG) spiega gli effetti di trovati da Siegel 2016

