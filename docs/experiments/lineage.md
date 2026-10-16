# Da quale sessione deriva quale

Le sessioni non sono indipendenti: ognuna estende una coorte precedente, e alcune sono costruite apposta per essere confrontabili tra loro. Questa pagina dice **cosa cambia da una all'altra** e **quali si possono mettere a confronto**. Il percorso di ogni sessione attraverso le pipeline è in [pipelines.md](pipelines.md), il dettaglio nel file della sessione.

```mermaid
flowchart TB
    classDef unused fill:#f0f0f0,stroke-dasharray: 4 4
    classDef pending stroke-dasharray: 5 5

    subgraph LES["Lesione — s1.x"]
        direction TB
        L11["<b>s1.1-vol</b> · 21-07<br/>1150 soggetti · 4 dataset"]
        L12["<b>s1.2-vol</b> · 27-07<br/>5269"]
        L13["<b>s1.3-vol</b> · 06-09<br/>5720 · mai usata a valle"]:::unused
        L14["<b>s1.4-vol</b> · 07-10<br/>5845 · 8 dataset"]
        L11 -->|"+ UCL-UK StrokeData"| L12
        L12 -->|"+ UKE/WAKEUP_acute"| L13
        L13 -->|"+ NEMESIS_T0,<br/>SFB936_ses01<br/>voxel fuori dal brain<br/>azzerati"| L14
    end

    subgraph SDC["Disconnettoma — s2.x"]
        direction TB
        S21["<b>s2.1-schaefer-200-tian-s2</b> · 26-08<br/>1119 · 232 regioni"]
        S22["<b>s2.2-vol</b> · 07-09<br/>1570"]
        S24["<b>s2.4-vol</b> · 07-10<br/>5845 · 8 dataset<br/>voxel fuori dal brain<br/>non azzerati"]
        S24N["<b>s2.4-vol</b> · 16-10<br/>5845 · 8 dataset<br/>voxel fuori dal brain<br/>azzerati<br/>non ancora costruita"]:::pending
        S24S["<b>s2.4-stream</b> · 07-10<br/>5831 · 87 tratti"]
        S21 -->|"+ UKE/WAKEUP_acute<br/>parcellata →<br/>voxel-wise"| S22
        S22 -->|"coorte piena"| S24
        S24 -->|"stessa coorte,<br/>voxel fuori dal brain<br/>azzerati"| S24N
        S24 -.->|"stessi dataset,<br/>altra rappresentazione,<br/>−14 senza alcun<br/>tratto colpito"| S24S
    end

    L13 <-.->|"stessa griglia 2mm,<br/>coorti diverse"| S22
    L14 <==>|"stessi 5845 soggetti,<br/>stesso ordine di riga,<br/>stesso trattamento<br/>dei voxel fuori dal brain"| S24N
    L14 <-.->|"stessa coorte,<br/>ma s2.4 senza<br/>azzeramento"| S24
```

## Cosa si può confrontare con cosa

- **s1.4-vol e s2.4-vol sono la stessa coorte**, lesione contro disconnettoma: stessi 8 dataset, stesso template 2mm, stessi 5845 soggetti nello stesso ordine di riga. È l'unica coppia su cui un confronto soggetto per soggetto è immediato.
- **Due matrici hanno il nome s2.4-vol, le distingue la data.** Quella del **07-10** ha i voxel fuori dal brain non azzerati (291345 colonne, 64110 delle quali fuori dalla maschera cerebrale) e quindi non è costruita come s1.4-vol (221955 colonne, azzerati). Quella del **16-10** è ricostruita con `correct_out_of_brain: true` (227235 colonne) ed è la vera controparte di s1.4-vol. Le due s2.4-vol non sono confrontabili voxel per voxel: stesse righe, colonne e valori diversi.
- **s2.4-stream** ha gli stessi dataset di s2.4-vol ma 14 soggetti in meno, quelli senza alcun tratto colpito: le righe **non** sono allineate per posizione.
- **s1.3-vol e s2.2-vol** condividono la griglia 2mm, quindi sono allineate voxel per voxel sulla griglia piena, ma le coorti sono diverse (5720 contro 1570) e le maschere di colonne non coincidono: va usato il `non_constant_mask.npy` di ciascuna, mai l'indice di colonna diretto ([s2.2-vol](s2.2-vol.md)).
- **s1.4-vol non è confrontabile voxel per voxel con le sessioni lesionali precedenti**: i voxel fuori dal brain sono stati azzerati su 1501 soggetti.
- **s2.1 e s2.2-vol** sono state costruite apposta con la stessa griglia di iperparametri, così l'unica variabile tra le due è la rappresentazione — 232 regioni contro 290940 voxel. La loro trustworthiness però **non si confronta**: ognuna misura la fedeltà al proprio spazio di input.

**s2.3-stream** non compare: era la streamline pensata quando UCL-UK non aveva ancora il CSV, e non esiste più come sessione a sé. È stata rifatta come s2.4-stream sulla lista di esclusioni attuale.
