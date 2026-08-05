Date: 24/06/2026
People: Professor Corbetta, Antonio, Sebastinao

---


## 1. Estensione della letteratura — lavori da includere

- **Bonkhoff** → clustering (stati dinamici di connettività)
- **Talozzi** → fase cronica
- **Siegel 2016** → asse comportamentale per predire le lesioni (rilevante anche per "Michael"/lavoro correlato)
- **Siegel 2018/2019** → deficit SDC vs deficit fMRI, e loro covarianza
- **Volpi et al.** → relazione tra variabili BOLD globali e locali
- **Sebastiano** (lavoro/collega, da specificare meglio)
- **D'Amico** → approccio "fingerprint"
- **Fallani** → clustering longitudinale

## 2. Domanda aperta centrale

**Non è chiaro come le feature locali si correlino con le alterazioni globali** → cioè, alterazioni locali del segnale come si legano a pattern di rete più ampi.

## 3. Segnale locale — quali feature considerare

- Ampiezza
- Covarianza
- ALFF (Amplitude of Low-Frequency Fluctuation)
- Regional homogeneity (quanto sono correlati i segnali tra voxel vicini)
- Media GFC / Varianza GFC (Global Functional Connectivity)
- Parametri locali in funzione della **distanza dalla lesione**

*Domanda di sintesi: quale di queste feature spiega meglio il comportamento?*

## 4. Pipeline FC (Connettività Funzionale) — proposta

1. Mappe funzionali → lesione
2. Identificazione di vari pattern di alterazione
3. Embedding a bassa dimensionalità (low-dimensional embedding)

**Obiettivo:** trovare alterazioni *canoniche* di connettività funzionale.

## 5. Ipotesi guida

- La struttura normale guida la FC → connettività normale solo lievemente alterata nel paziente
- Approccio: calcolare la connettività del singolo paziente come **z-score rispetto al pattern normativo** (gruppo di controllo/normale)

---

Vuoi che approfondisca qualche punto (es. come collegare Volpi/Siegel al vostro pipeline SDC, o come strutturare l'analisi z-score)?

Date: 24/06
People: Professor Corbetta, Sebastiano and Antonio

# Feature space

**Objectives**: multimodal relation across modalities 

**Task1**:

- n=4000
- Low dim embedding lesions —> visualizzazione spaziale
- Clustering across lesions —> topographic clustering

**Task2**:

- n=3000
- Low dim embedding lesions di SDC

**Task3**:

- Clustering across n= 500 patients with fMRI  (WU+PD+fri).
- Calculate fMRI matrices differences compared to healthy (subtraction).
- Relation of matrices with clustering
- So for each subject:
  - multiscale realtiionship between FDC and SDC pattern
  - commn patter /cluster anlysis

**Task4**:

- n=80 (Padova)
- EEG features calculation: frequency band map differences (stroke versus healthy) .
- Embedding

**Task5**:

- n=60 
- correlation with Behavioural
- multismodal and multiscale features and behavioral correlates

+ demo/ana

Note

- 3/4 lavori possbili
