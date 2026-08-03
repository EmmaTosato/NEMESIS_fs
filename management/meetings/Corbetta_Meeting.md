Date: 29/07/2026
People: Professor Corbetta

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
