# Changelog dei metodi

Decisioni su **come analizziamo**: proxy per variabili mancanti, feature calcolate, soglie, metodi adottati o abbandonati — con le alternative scartate e il perché.

**Cosa NON va qui**: i risultati di un esperimento (`docs/experiments/`), i parametri di una singola run (`runs.csv`), il funzionamento corrente di una pipeline (`docs/`, sempre al presente).

Voci in ordine cronologico inverso.

---

## 07-10-26 — Matrice lesionale `s1.4-vol` costruita con `correct_out_of_brain: true`

**Decisione**: `07-10_s1.4-vol` è la prima matrice lesionale costruita con la correzione dei voxel fuori dal brain attiva (`brain_mask_path` = maschera res-2). I voxel di lesione fuori dalla maschera cerebrale sono azzerati e il soggetto resta in matrice, con `lesion_volume_voxels` ricalcolato sui dati corretti.

**Numeri**: 5845 soggetti × 221955 feature (5853 − 8 esclusi da `excluded_subjects.csv`, `scope=all`: 3 `empty_mask`, 5 `out_of_brain_fraction_too_high`). **1501 soggetti corretti** (25,7%): 177031 voxel azzerati in totale, mediana 18 voxel per soggetto, massimo 2938, 361 soggetti con almeno 100 voxel.

**Perché**: un voxel fuori dal cervello non è lesione, quindi non deve entrare né nelle feature né nel volume. Le esclusioni per frazione >30% togliono i casi troppo contaminati (i 5 esclusi hanno frazione 0,41–1,0; con la correzione `sub-STUNIPD0558`, frazione 1,0, sarebbe diventato una riga tutta a zero); sotto soglia si corregge invece di escludere.

**Alternativa scartata**: lasciare la correzione spenta. Terrebbe la matrice confrontabile voxel per voxel con `s1.1`–`s1.3`, ma lascerebbe in matrice voxel fuori dal brain per 1501 soggetti.

**Conseguenza ancora vera oggi**: `s1.4-vol` **non è confrontabile voxel per voxel** con `s1.1-vol`, `s1.2-vol`, `s1.3-vol`: costruite prima del 29-09-26, quando il flag non esisteva (`e7ba077`), quindi senza alcuna correzione. Vale per ogni confronto di risultati di `dim_reduction`/`clustering` tra le sessioni: la differenza può dipendere dalla correzione e non solo dai dataset in più.

---

## 07-10-26 — Sede della lesione: sovrapposizione corticale/bianca come categoria a parte (opzione C); layout in `lesion_metadata.csv`, solo 2 mm

**Decisione**: i voxel che HO corticale chiama corteccia e HO sotto-corticale chiama `Cerebral White Matter` non vanno né alla corteccia né alla bianca: formano una **settima categoria**, `cortex_white_boundary`. Le sette: infratentoriale, sotto-corticale grigia, `cortex_only`, `cortex_white_boundary`, `white_matter_only`, ventricolo, non etichettato (infratentoriale e sotto-corticale grigia restano prioritarie su tutto).

**Alternative scartate**: (A) corteccia prioritaria, com'era: sposta la classe "corticale pura" più di ogni altra scelta e non ha un motivo forte; (B) bianca prioritaria: stesso arbitrio specchiato; (D) HO corticale a soglia 50% invece di 25%, per ridurre la sovrapposizione alla fonte: tenuta in riserva, cambierebbe un atlante già deciso e non so se il pacchetto FSL lo contiene (non verificato). Provenienza: i due atlanti sono due file HO distribuiti separatamente, i bordi non sono garantiti coerenti; la fascia corticale a thr25 è generosa.

**Layout in `assets/metadata/lesion_metadata.csv`** (non ancora implementato, nulla in `src/`): da 10 a 18 colonne, **solo a 2 mm**. `location_dominant_2mm` (la categoria con la frazione più alta, vuota con maschera vuota) più sette frazioni `location_<categoria>_2mm` sulla lesione dentro il brain mask (denominatore: `lesion_volume_voxels_2mm`). Scartate: una sola colonna di etichetta senza frazioni (una lesione tocca quasi sempre più aree: a >10% il 63% ne tocca due, il 7% tre; l'etichetta non permette di ricostruire le quote); etichette a soglia nel file (le soglie non sono decise, scriverle le congelerebbe).

**Solo 2 mm, per ora, perché la sede a 1 mm non serve** (motivo dato dall'utente): niente colonne `_1mm` di sede. Il 1 mm resta controllo del prototipo e dei test. Il codice di `compute_lesion_metadata` assume le stesse colonne per ogni griglia: avere la sede solo a 2 mm richiede di cambiarlo (sette colonne più l'etichetta contro le quattro attuali per griglia).

**Non deciso**: la regola per la parità tra due categorie nell'etichetta prevalente (frequente nelle lesioni di pochi voxel): proposta, non confermata, vince la categoria con la precedenza più alta. Soglie di coinvolgimento e di "pura" ancora aperte (`open_problems.md`).

---

## 07-10-26 — Sede della lesione: classificazione sulla griglia a 2 mm, 1 mm come controllo; prima misura sull'intera coorte

**Decisione (OK dell'utente, 07-10-26)**: le frazioni per categoria si calcolano sulla **griglia a 2 mm** (quella di produzione); la griglia a 1 mm resta solo un controllo. **Scartato**: classificare a 1 mm. Motivo: per WashU/UKLFR (e probabilmente NEMESIS_T0/SFB936) le maschere a 1 mm sono ricampionamenti delle originali (2 mm / 1,5 mm) con scarti di 0,5-1,2 mm in y/z e volume ×1,09 / ×0,85, mentre a 2 mm ricostruiscono l'originale; le PSP frazionarie perdono voxel a 1 mm con `> 0,5`.

**Popolazione**: tutte le 5853 maschere in `lesion_metadata.csv` sono state calcolate; si classificano **5845**, cioè fuori solo le 8 righe di `excluded_subjects.csv` con `scope = all`. Le 14 righe con `scope = sdc-streamline` hanno lesioni valide (la loro esclusione riguarda solo la matrice SDC streamline) e restano. Interpretazione mia di "escludendo excluded_subjects.csv", da confermare. Nessuno dei 5845 ha 0 voxel dentro il brain a 2 mm; 27 hanno meno di 5 voxel (mediana 434).

**Controlli sull'intera coorte (tutti i 5853, entrambe le griglie)**: volume dentro il brain mask = volume di produzione 5853/5853; frazione fuori dal brain = produzione 5853/5853; somma delle categorie = volume 5853/5853. Lato dell'atlante = `lesion_side_2mm` in 5465/5483 decidabili (68 `both` e 7 vuoti non decidibili), 1 mm 5493/5511; con L/R scambiati l'accordo crolla a 18/5483 (il controllo può fallire). Le 18 discordanze a 2 mm non sono state esaminate.

**Misurato (2 mm, n = 5845)**:
- Frazione media: corticale 0,309, sotto-corticale grigia 0,114, infratentoriale 0,103, bianca 0,444, ventricolo 0,004, non etichettato 0,026. Categoria dominante: bianca 2551, corticale 2117, infratentoriale 643, sotto-corticale 507, non etichettata 27. 121 lesioni hanno >20% non etichettato.
- Quota "pura" (frazione dominante ≥ t): 0,935 (t=0,5), 0,734 (0,6), 0,543 (0,7), 0,378 (0,8), 0,246 (0,9). Nessun plateau, il calo è graduale (−20, −19, −17, −13 punti): la sweep non indica una soglia naturale.
- Quota "coinvolta" (frazione > m): a m=0 corticale 0,678, sotto-corticale 0,502, infratentoriale 0,180, bianca 0,870; a m=0,10: 0,557 / 0,270 / 0,126 / 0,813. A 0 la sotto-corticale è instabile (0,502 contro 0,270 a 0,10), conferma la proposta provvisoria di partire da >10%. A >10% le categorie anatomiche coinvolte sono 1 nel 30,3%, 2 nel 62,8%, 3 nel 6,7%.
- Per dataset (`out/cohort_dataset_summary.csv`) la composizione è molto diversa: dominante corticale UKLFR 64%, PASPORT 69%, UCL-UK 31%; lesioni con infratentoriale >10% UKLFR 0,1%, PASPORT 0%, contro 15-18% di UCL-UK/WashU/SFB936. Perché UKLFR/PASPORT non abbiano lesioni infratentoriali (selezione della coorte?) non è verificato.

**Sovrapposizione corticale/bianca di HO: misurata, e pesa.** Quota della lesione in voxel reclamati da entrambe: media 0,046, mediana 0,023, p90 0,119, max 0,70; 836 soggetti sopra 0,10. Dando la precedenza alla sostanza bianca invece che alla corticale: la categoria dominante cambia in 455/5845 (7,8%; per dataset da 1,8% a 10,7%); le lesioni "pure corticali" scendono da 905 a 511 a t=0,7 (da 1972 a 1496 a 0,5; da 200 a 101 a 0,9); "corticale coinvolta" a >0,10 da 3255 a 3098. La precedenza corticale > bianca, scelta il 06-10-26 senza misurarne l'effetto, è quindi la leva che più sposta la classe "corticale pura". Non è stata cambiata.

**1 mm contro 2 mm**: la categoria dominante differisce in 143/5845 (2,4%; per dataset 1,5-2,7%, per header LAS+90 2,6% / RAS −90 1,7% / RAS −91 2,5%); |Δfrazione| massima per soggetto: mediana 0,017, p95 0,072, max 0,48. L'etichetta (dominante, pura) differisce per 268 / 422 / 307 soggetti (4,6 / 7,2 / 5,3%) a t = 0,5 / 0,7 / 0,9. **Limite del controllo**: confronta due griglie della *stessa* maschera locale, non maschera locale contro originale (le originali a 2 mm di WashU non sono in locale), quindi non dice se il ricampionamento a 1 mm di WashU/UKLFR sposti la sede; dice solo che 1 mm e 2 mm raccontano la stessa storia per oltre il 97%.

**Conseguenza ancora vera**: le soglie e la precedenza corticale/bianca restano **non decise** (`open_problems.md`); nulla è in `src/`. Script e numeri completi in `tmp/lesion_location/` (`07_cohort_counts.py` → `out/cohort_counts.csv`; `08_cohort_summary.py` → `out/08_summary.txt`), locale, gitignored.

---

## 07-10-26 — Header RAS −90: nessuna traslazione in x rispetto alle originali; T1 non utilizzabili

**Fatto**: un agente sul cluster (sola lettura) ha trovato che per UNIPD/WashU le T1 sono native (nessuna in MNI, per nessun gruppo di header, in nessun dataset) e non esiste alcuna trasformazione native→MNI: il test T1→template non è eseguibile. Ha invece confrontato i baricentri delle maschere locali con le `manual_masks` originali (tabella in `open_problems.md`): per WashU la differenza in x ha mediana +0,05 mm (sd 0,98), quindi nessuna traslazione di 1 mm in x; in y/z restano scarti di 0,5-1,2 mm e il volume cambia (×1,09 WashU, ×0,85 UKLFR), compatibili con un ricampionamento da 2 mm (WashU) o 1,5 mm (UKLFR). Per PASPORT e PSP il confronto dà 0,000 (calibrazione: il metodo funziona).

**Decisione**: nessuna correzione dell'header; il problema "traslazione di 1 mm in x" è considerato non supportato (insieme al test sui bordi del cervello della voce precedente). Resta aperto l'effetto del ricampionamento a 1 mm per i 4 dataset RAS −90.

**Non verificato da me**: i numeri sono del report dell'agente; l'origine delle maschere locali per ciascun dataset (copia `lesion` di BCBToolKit) è dedotta dal `data_changelog.md`, non controllata sul server.

---

## 06-10-26 — Header RAS −90: test statistico inconclusivo, header lasciato come verità

**Decisione**: le 1032 maschere con header RAS −90 restano trattate col loro header (nessuna traslazione applicata).

**Fatto**: per 5852 maschere (una vuota esclusa) si sono spostati i soli voxel lesionali di −3..+3 mm lungo x (y e z come controlli negativi) contando quelli fuori dal brain mask del template a 1mm. Ipotesi testata: griglia vera = −91 (identica al template), quindi minimo atteso a −1 mm in x per i 4 dataset RAS −90. Osservato: minimo a +1 (UKLFR, SFB936), +2 (NEMESIS_T0), −1 (WashU); sul gruppo intero la frazione fuori dal brain è 0,0463 a −1, 0,0422 a 0, 0,0421 a +1. Gruppi di riferimento: WAKEUP (identico al template) minimo a +1, LAS +90 (4370) a 0 con stima sub-voxel −0,26. Assi di controllo: minimi a ±1-2 mm in y e z in più dataset (WashU y=2, z=2; NEMESIS_T0 y=1).

**Perché inconclusivo**: il criterio "fuori dal brain mask" ha risoluzione di circa ±1-2 mm, perché i cervelli normalizzati differiscono dal template di più di 1 mm e la distribuzione delle lesioni vicino al bordo non è simmetrica; un controllo che sbaglia di ±1 mm sul gruppo di riferimento e sugli assi di controllo non può rivelare uno spostamento di 1 mm. Non conferma la traslazione ipotizzata (il minimo non è a −1) ma non la esclude.

**Conseguenza ancora vera**: l'unico controllo decisivo resta la T1 normalizzata sul server o l'informazione su come sono state scritte le maschere (`open_problems.md`). Script in `tmp/lesion_location/06_header_shift_test.py` (locale, gitignored).

---

## 06-10-26 — Sede della lesione: atlanti FSL e sei categorie esclusive (prototipo in `tmp/`, non ancora in `src/`)

**Decisione**: ogni lesione si classifica per sede con tre atlanti FSL, in `assets/atlases/fsl/` (provenienza nel suo `README.md`): Harvard-Oxford corticale (48 etichette), Harvard-Oxford sotto-corticale (21), Cerebellum-MNIfnirt (28), tutti `maxprob-thr25` a 1mm e 2mm. Sei categorie esclusive per voxel dentro il brain mask, in ordine di precedenza: infratentoriale (`Brain-Stem` HO + cervelletto) > sotto-corticale grigia (talamo, caudato, putamen, pallido, ippocampo, amigdala, accumbens) > corticale > sostanza bianca (`Cerebral White Matter` HO) > ventricolo > non etichettato. Per lesione si tengono le **frazioni continue** per categoria (sui voxel lesionali dentro il brain mask) e la quota fuori dal brain mask a parte; le etichette discrete si derivano dopo, a soglie diverse. Il tronco encefalico intero conta infratentoriale. Anteriore/posteriore: **messo in stop**.

**Alternative scartate**: AAL3 (un solo file con cervelletto e vermis, ma costruito sul template Colin27, un MNI diverso: rischio di disallineamento proprio nel cervelletto); SUIT (spazio proprio, scomodo per lesioni già in MNI); Schaefer/Yan + Tian (già in locale, ma parcellazioni funzionali, e Tian non ha cervelletto né tronco); Arterial Territories Atlas (Liu et al. 2023, NITRC, CC-BY): rinviato, serve al circolo anteriore/posteriore, cioè alla parte in stop. JHU per la sostanza bianca profonda: non ora, HO la separa già.

**Misurato (prototipo, 48 soggetti = 6 per dataset, seed 0)**: gli atlanti sono LAS, i template RAS; la corrispondenza di griglia è un flip x con offset intero (181 a 1mm, 90 a 2mm), quindi il ricampionamento `nearest` tramite affine è senza perdite (conteggi per etichetta identici). Segno emisferico in coordinate mondo corretto per tutte le etichette Left/Right; un flip naive dell'array viene rilevato (20 violazioni per atlante). Controlli contro `lesion_metadata.csv`: frazione fuori dal brain 48/48; volume dentro il brain mask 48/48 (il volume di produzione è post-correzione); lato 46/46 sui decidibili (2 lesioni solo di tronco non hanno etichette L/R); categoria dominante uguale a 1mm e 2mm in 47/48. Volumi delle categorie a 1mm: corticale 1.035.841, sotto-corticale 63.699, infratentoriale 204.154, bianca 389.870, ventricolo 10.705, non etichettato 122.974 (brain mask 1.827.243). Sovrapposizioni tra atlanti: corticale/infratentoriale 2.440 voxel, corticale/sotto-corticale 485, corticale/bianca 109.621 (la fascia corticale HO è generosa al confine); sui 48 soggetti solo lo 0,08% dei voxel lesionali (max 1,9%) cade in voxel reclamati da più di una tra corticale/sotto-corticale/infratentoriale. L'effetto della sovrapposizione corticale/bianca sulle lesioni **non è misurato**.

**Soglie: non decise.** La letteratura non ha uno standard per la quota *della lesione* in una categoria: la pratica clinica classifica per coinvolgimento (sotto-corticale / cortico-sottocorticale / corticale) senza percentuali; le soglie quantitative trovate sono sulla frazione della *regione* danneggiata (>0, >1, >10, >20%), un'altra quantità (solo riassunti di ricerca, paper non letti per intero). Nel campione "pura" = 43/48 a soglia 50%, 31 a 60%, 23 a 70%, 13 a 80%, 8 a 90%, senza salto naturale. Da decidere con una sweep sull'intera coorte; proposta provvisoria: coinvolgimento a >10% della lesione (a >0% è instabile: la corticale tocca 38/48 contro 29/48).

**Conseguenza ancora vera**: (1) il gruppo di header RAS −90 (1032 maschere, vedi la voce SDC qui sotto) è trattato col suo header come verità; se fosse sbagliato di 1 voxel la categoria dominante cambia in 1 soggetto su 24 (max |Δfrazione| 0,08), aperto in `open_problems.md`. (2) Le 168 maschere PSP sono frazionarie e a 1mm la binarizzazione `> 0,5` ne perde voxel (`open_problems.md`): le frazioni di PSP a 1mm sono indicative. (3) Mesencefalo: il tentorio lo taglia, HO non permette di dividerlo, il tronco intero conta infratentoriale.

---

## 06-10-26 — Disconnessione per soggetto su due griglie (2mm e 1mm), come il volume lesionale

**Decisione**: `sdc_metadata.csv` ha le due colonne (`disconnection_load_voxels_<g>`, `disconnection_mean_<g>`) su **2mm e 1mm**, config `grids` come `compute_lesion_metadata.json`; `enrich_metadata.json` copia nel registro entrambe le griglie sia per la disconnessione sia per il volume lesionale (`lesion_volume_voxels_1mm` prima restava solo in `lesion_metadata.csv`). L'Embedding Explorer offre la scelta 1mm/2mm (default 2mm) per volume, disconnection load e mean disconnection.

**Perché**: la voce "Disconnessione per soggetto: carico/media" qui sotto aveva fissato la sola griglia 1mm senza alcun confronto con il 2mm: era la risoluzione nativa delle mappe (`res-1` nel nome del file), non una scelta di risoluzione deliberata, mentre la griglia di produzione del progetto è 2mm (voce 06-09-26 sulle griglie delle matrici). Richiesto esplicitamente di avere entrambe, non di sostituire l'una con l'altra.

**Misurato sull'intera coorte (5853 soggetti, 19m54s di run)**: il carico a 2mm ordina i soggetti quasi come quello a 1mm (Spearman 0,9999994); `8 × carico_2mm / carico_1mm` ha mediana 1,001, intervallo 0,989-1,017, quindi `nearest` a 2mm sottocampiona ma la mappa è abbastanza liscia da non cambiare il numero in modo sensibile; la media sul cervello coincide (rapporto mediano 1,000). Nessun soggetto sparisce nel ricampionamento: l'unico con carico 0 (`sub-STUKLFR0671`) è 0 su entrambe le griglie, a differenza del volume lesionale dove una lesione piccola può azzerarsi a 2mm.

**Conseguenza ancora vera**: il `csv` è stato rigenerato con `overwrite: true` da una copia del config nella scratchpad; il config del repo resta `overwrite: false`. I valori sono a precisione piena, senza arrotondamento: il `round(…, 3)` introdotto in giornata è stato tolto (a 3 decimali la media a 1 mm aveva 229 valori distinti su 5853 e 26 soggetti a `0.000`; senza, 5853 distinti) e il csv è stato ricalcolato su entrambe le griglie (20m25s). I nomi delle colonne dell'app (`DEFAULT_GRID`, `grid_column`, `available_grids` in `src/analysis/embedding_coloring.py`) sostituiscono i vecchi `*_volume_grid*`: nessun alias.

---

## 06-10-26 — Criteri di esclusione dalle matrici: nessuna esclusione per lesione piccola, soglia > 30% fuori dal brain

**Decisione**: (1) le lesioni piccole **non** si escludono: anche una lesione focale o minima può avere conseguenze cliniche gravi, quindi il volume non è un proxy di rilevanza clinica; per volume si scarta solo la maschera vuota (`empty_mask`, 3 soggetti). Il motivo `lesion_too_small` resta nel vocabolario ma non è usato. (2) Si escludono i soggetti con **più del 30%** dei voxel di lesione fuori dalla maschera cerebrale (`out_of_brain_fraction_2mm`, misurata prima dell'azzeramento), motivo `out_of_brain_fraction_too_high`.

**Verificato su `lesion_metadata.csv`/`excluded_subjects.csv`**: 5 soggetti sopra il 30%, tutti e soli quelli esclusi per questo motivo (frazione minima 0,41); tra i non esclusi il massimo è esattamente 0,30, quindi la soglia è stretta (`>`). Tra gli inclusi il volume minimo a 2 mm è 1 voxel, 122 soggetti stanno a 10 voxel o meno.

**Perché**: la voce del 29-09-26 ("Esclusione dei soggetti: lista curata a mano al posto delle soglie in config") spiega perché non esiste una soglia automatica sui dati (nessun salto naturale); la 30% è un criterio di analisi applicato a mano quando si compila il config, non un parametro di pipeline. Sotto la soglia il soggetto resta; i voxel fuori dal brain sono azzerati solo con `correct_out_of_brain: true`, flag che resta configurabile (`true` o `false`) in `build_lesion_matrix.json`.

**Config ripristinato nella stessa sessione**: `build_lesion_matrix.json` aveva `excluded_subjects_path` assente (tolto da `4b297d3`) e due chiavi morte `min_lesion_volume_voxels`/`max_out_of_brain_fraction` a `null`; il loader sollevava `missing required field 'excluded_subjects_path'`. Chiavi morte cancellate, `excluded_subjects_path` rimesso.

**Conseguenza ancora vera**: la regola è documentata in `docs/dev/metadata.md` ("Criteri di esclusione adottati") e `docs/guides/metadata.md`; la pipeline non la applica, quindi un soggetto nuovo sopra il 30% entra in matrice finché non è aggiunto a mano al config.

---

## 06-10-26 — Disconnessione per soggetto: carico/media come analogo del volume lesionale

**Decisione**: `assets/metadata/sdc_metadata.csv` (nuova pipeline `compute_sdc_metadata.py`, `src/features/sdc.py::compute_sdc_metadata`) misura, per ogni soggetto con disconnettoma (5853/5853), due colonne sulla griglia 1 mm: `disconnection_load_voxels_1mm` (somma della probabilità di disconnessione sui voxel dentro il cervello) e `disconnection_mean_1mm` (la stessa somma divisa per il numero di voxel cerebrali, costante di griglia — le due ordinano i soggetti in modo identico). `enrich_metadata.py` le copia in `participants.csv` (blocco `sdc_metadata`, stesso meccanismo di `lesion_metadata`, join stretto su `has_sdc`); l'Embedding Explorer le offre come due bottoni di colore, scala lineare.

**Alternative scartate**: volume sogliato a `p > 0.5` (la soglia che il pannello "Disconnessione per cluster" dell'app già usa — su 200 soggetti ordina quasi come la somma, Spearman 0,993, ma è una soglia in più da giustificare e introduce zeri assenti dalla somma); `n_nonzero_voxels` di BCBToolKit (misura quanto si *diffonde* la disconnessione, non quanta ce n'è: il minimo non nullo è costante a 1/178, un solo donatore su 178, quindi conta qualunque traccia — mediana 36% del cervello, fino al 91%); `map_mean_nonzero` (intensità con denominatore per-soggetto, non un carico); leggere `mapstats.tsv` di BCBToolKit invece di aprire i NIfTI (`map_sum` coincide al decimale col ricalcolo, verificato su 5 soggetti, ma non è mascherato sul cervello e non permette soglie).

**Scoperta corretta prima di entrare in `src/`**: le mappe disconnettoma non condividono un reticolo di voxel. Censimento sull'intera popolazione (5853 header, letti senza aprire i dati): 3 affine distinti per dataset — LAS con offset x `+90` (UCL-UK/PASPORT/PSP, 4370 soggetti), RAS con `-90` cioè traslato di 1 voxel (UKE-SFB936/UKLFR/NEMESIS_T0/WashU, 1032), RAS con `-91` identico al template MNI (UKE-WAKEUP, 451). Un primo prototipo assumeva uno specchio fisso dedotto da un campione di 6 soggetti per caso in maggioranza LAS: corretto per 4370, speculare per gli altri 1483, senza errore (`.claude/lessons_learned.md` #40). Ogni mappa viene ora portata sulla griglia di riferimento col **suo** header (`resample_to_img`, `nearest`), mai con un flip o un'identità presunti.

**Verificato**: somma ricalcolata contro `map_sum` di BCBToolKit, scarto 0.0 su 5 soggetti; riallineamento verificato con un calcolo geometrico indipendente per gruppo di header, scarto 0.0 su 12 soggetti (4 per gruppo); quota di massa fuori dal cervello misurata su 400 soggetti casuali (mediana 0,80%, max 8,9%) invece di stimata sui 5-6 soggetti del prototipo iniziale. Run di produzione: 5853/5853 soggetti, 18m24s, nessun NaN.

**Conseguenza ancora vera**: scala **lineare**, non log come il volume — misurato sull'intera coorte, asimmetria del carico 1,5 e massimo/mediana 7,6, contro 4,1 e 97 per il volume lesionale; un log sovra-correggerebbe (asimmetria del log10 -0,8). Un carico di 0 è un valore vero (nessuna disconnessione), non un "missing" come il volume a 0 sulla griglia 2mm.

---

## 06-10-26 — Forzatura del lato geometrico (WashU) spenta; controlli sulle immagini sui 15 disaccordi

**Decisione**: `geometric_override_datasets` in `config/pipelines/enrich_metadata.json` da `["UNIPD/WashU"]` a `[]`, `enrich_metadata` rilanciato: cambiano esattamente le 11 righe WashU (`lesion_side` e `lesion_side_source` tornano al valore del tsv, `clinical`), nient'altro. La funzione resta nel codice, spenta (testata, riattivabile).

**Perché**: la voce precedente mostra che i test comportamentali (ARAT, 9HPT) danno ragione all'etichetta in 6 degli 8 casi decidibili: forzare la maschera scriveva il lato sbagliato nella maggioranza dei casi. **Alternativa scartata**: tenere la forzatura accesa in attesa di prove sulla T1: le prove sulle T1 non sono arrivate (sotto).

**Controlli sulle immagini, svolti da un agente sul cluster (sola lettura, T1 non presenti in locale)**:
- lesione nativa e maschera MNI stanno dallo stesso lato in tutti gli 11 WashU (`sform` e `qform` concordi): la normalizzazione non inverte;
- nessuna proprietà degli header delle T1 native (orientamento RAS/LAS, segno del determinante, software di conversione, scanner) distingue gli 11 da 20 controlli concordi (8 RAS e 3 LAS contro 16 e 4);
- contrasto maschera/specchio sulla T1 in MNI (griglia a 2 mm): controlli tra -0,18 e +0,11 (mediana -0,05); 10 degli 11 dentro quell'intervallo, solo `sub-STUNIPD0187` a +0,51. Non discrimina;
- le nostre maschere locali sono l'output SDC a 1 mm (`features/.../lesion/<sub>/..._res-1_...`), non le `manual_masks` del server, che sono sul reticolo originale a 2 mm (circa un ottavo dei voxel); i 15 md5 locali coincidono con i file `res-1` (riferito dall'agente). Il confronto con il server mostra `sub-STUKLFR0403`: maschera manuale a sinistra (7300 voxel; lato dell'etichetta e dell'afasia), maschera SDC a destra (27984 voxel). Per gli 11 WashU manuale e SDC stanno dallo stesso lato;
- sette soggetti WashU (`0222`, `0179`, `0187`, `0216`, `0233`, `0242`, `0251`) hanno la T1w con identici `AcquisitionTime` (11:31:53.6725), orientamento DICOM, scanner (Prisma_fit) e shape: probabilmente la stessa immagine assegnata a più soggetti. Non verificato sui dati.

**Conseguenza ancora vera oggi**: i controlli sulle immagini non decidono il lato. Resta un'ipotesi non verificata sul dove nasca l'inversione per gli 11 WashU. Aperti: confronto manuale/SDC su tutti i soggetti (controllo E), identità delle 7 T1 (controllo F), maschere capovolte nelle matrici.

## 06-10-26 — Controlli E e F: il passaggio SDC non spiega gli 11 WashU; le "7 T1 identiche" sono un artefatto di metadato

**Fatto**: i due controlli lasciati aperti dalla voce precedente, eseguiti da un agente sul cluster (sola lettura, T1 non presenti in locale).

**Controllo E** (lato world di manuale vs SDC, su ogni soggetto con entrambe le maschere in MNI): WashU 1/195 discorde (`sub-STUNIPD0094`), UKLFR 3/673 (`sub-STUKLFR0253`, `0403`, `0463`), PSP 0/168, PASPORT 0/83; UKE 0 soggetti con entrambe le maschere disponibili sul server; `NEMESIS_T0` non esiste come cartella. MD5 dei 15 file locali contro l'SDC (`res-1`) del server: match su tutti e 15 — confermato su tutta la popolazione, non solo sul campione, che i file locali sono l'output SDC e non le `manual_masks` originali.

**Conseguenza**: il passaggio SDC inverte il lato raramente (0,2-0,5% dove misurabile) e **non per nessuno degli 11 WashU in disaccordo** (`sub-STUNIPD0094` non è tra gli 11). Non è il meccanismo dell'inversione.

**Controllo F** (identità delle T1 con `AcquisitionTime`/orientamento/scanner identici): il gruppo da 104 soggetti (che includeva le 7 segnalate) condivide un timestamp **placeholder** nel JSON ma ha dati anatomici tutti distinti (md5 e array diversi per ogni coppia) — un artefatto di metadato statico, non immagini duplicate. Trovate invece, per caso, due coppie di T1 realmente identiche byte per byte ma con `lesion_roi` diverso: `sub-STUNIPD0053`/`0060` e `sub-STUNIPD0066`/`0077`.

**Perché conta**: `sub-STUNIPD0077` è uno degli 11 WashU in disaccordo (maschera capovolta secondo il test comportamentale di questa stessa giornata). Condividere la T1 nativa con un altro soggetto (`0066`), con una maschera di lesione diversa sopra, è un'anomalia di dati reale nel sottoinsieme che ci interessa — non spiega di per sé l'inversione, ma non è capita.

**Non verificato**: se le due coppie di T1 duplicate siano uno scambio di identità tra soggetti o un placeholder riusato quando lo scan originale manca. Nessuna conseguenza per la decisione di spegnere la forzatura (voce precedente): resta valida.

## 06-10-26 — Verifica del lato forzato (WashU) con test comportamentali; soglia a 1 mm verificata; calibrazione rifatta

**Cosa è stato fatto**: (1) verificata l'ipotesi della voce del 05-10-26 (sbaglia l'etichetta clinica, non la maschera), senza T1 locali, con deficit controlaterali presenti nei tsv; (2) esteso il controllo ai disaccordi degli altri dataset su dati completi; (3) rifatta la calibrazione della soglia, a 2 mm e a 1 mm.

**Metodo e risultati del punto 1-2**: WashU `ARAT_L/R` e `9HPT_L/R`: la mano più debole indica il lato della lesione (controlaterale). Calibrazione del test sui 151 soggetti con etichetta e maschera concordi: ARAT 90/92 (98%), 9HPT 102/119 (86%, valore alto = meglio). UKE: `NIHSS_5a/5b` + `6a/6b` sui 409 concordi, 259/273 (95%). UKLFR: afasia (`NIHSS_9 ≥ 1`) nei destrimani con etichetta e maschera concordi, lesione sinistra in 128/129 (99%). Applicati ai 15 disaccordi pieni: **etichetta giusta in 8, maschera giusta in 3, non decidibili 4** (WashU: 6/2/3; UKE e UKLFR: 2/1/1). Sui 9HPT degli 11 WashU, 5 dei 6 informativi indicano l'etichetta: sotto "maschera giusta" la probabilità di quel risultato è ~3e-4 (accuratezza di base 86%, indipendenza assunta). In WashU il disaccordo è associato alla manualità (mancini 5/16, destrimani 6/146, Fisher p = 0,0016). Numeri completi dei disaccordi a 2 mm: WashU 11/162, UKLFR 2/700, UKE-WAKEUP 2/411, PSP 0/94, UKE-SFB936 0/53 (i campioni citati prima, 1/120 e 1/95, erano stime).

**Conclusione**: l'assunzione della forzatura è contraddetta dai dati nella maggior parte dei casi decidibili: la regola `geometric_override_datasets` scrive il lato sbagliato in 6 casi su 8 decidibili WashU. Non rimossa in questa voce: la decisione spetta all'utente (vedi `.claude/open_problems.md`). Conseguenza non voluta: le maschere capovolte sono nelle matrici (lesione, SDC).

**Soglia a 1 mm** (`calibrate_lesion_side_threshold.py`, verità = `participants.csv` salvato prima della forzatura, con gli 11 ancora `clinical`): 2 mm con tutti e 5 i dataset, 1445 soggetti, soglia 0.20 → **97,4%** (identico alla calibrazione del 28-09-26; ottima 0.28, 97,5%). Senza PSP, sugli stessi 1350 soggetti: 97,3% a 1 mm e a 2 mm, **stesso lato per tutti i 1350**, 97,4% a 0.28 su entrambe. Senza le 15 inversioni piene (non correggibili da nessuna soglia) 98,4%. La soglia vale quindi a 1 mm. La classe `both` resta debole (24 etichette cliniche, 3 predette).

**Script rotto, ripristinato**: `calibrate_lesion_side_threshold.py` importava `KNOWN_LESION_SIDES` da `src/features/lesion.py`, cancellata il 29-09-26 (commit `cf6e1fe`) e mai ripristinata: falliva all'import e nessun test lo copriva. Ripristinata la costante, aggiunto `tests/unit/test_calibrate_lesion_side_threshold.py` (5 test).

## 05-10-26 — `lesion_side` di WashU: dove clinico e maschera sono opposti, il registro prende la geometria

*(Spenta il 06-10-26: vedi la voce sopra. Il testo che segue descrive la decisione com'era allora.)*

**Decisione**: in `participants.csv`, per i dataset di `geometric_override_datasets` (oggi solo `UNIPD/WashU`, `config/pipelines/enrich_metadata.json`), un soggetto con lato clinico `left`/`right` e lato in `lesion_side_2mm` l'opposto riceve il lato **geometrico** e `lesion_side_source = "geometric"`. È l'unica eccezione a "un valore clinico non si sovrascrive". Un `both` geometrico non scatta mai.

**Misurato**: su 162 WashU con lato clinico, 11 (6,8%) sono opposti alla maschera, 6 `left`→`right` e 5 `right`→`left`, tutti con `|laterality_index_2mm| ≥ 0,95`. Le 195 maschere WashU hanno header identico (RAS, affine con origine -90, shape 182×218×182). Negli altri dataset il tasso è quasi nullo (UKLFR 0/120, UKE 1/120, PSP 1/95, campioni di `.claude/open_problems.md`). Applicato alla run del 05-10-26: i 11 soggetti sono `sub-STUNIPD0002/0008/0026/0056/0077/0131/0147/0151/0179/0187/0222`.

**Perché**: l'ipotesi è che sbagli l'etichetta clinica (errore alla fonte, magari una convenzione di visualizzazione radiologica), non la maschera. Il motivo per preferire questa ipotesi: un capovolgimento delle maschere sarebbe sistematico per un processo comune a tutto il dataset, non confinato a 11 soggetti in entrambe le direzioni. **Non è verificata sulla T1** (verificata con test comportamentali il 06-10-26: la contraddicono, vedi voce successiva).

**Alternative scartate**:
- *Elenco di ID in config*: va rifatto a mano a ogni cambio delle maschere e non dice perché quei soggetti. La regola si rilegge da `lesion_metadata.csv` a ogni run.
- *Regola globale su tutti i dataset*: UKE e PSP hanno un caso ciascuno, mai indagati; un default globale cambierebbe il registro su dati che nessuno ha guardato.
- *Lasciare il lato clinico e usare la geometria solo dove manca* (comportamento precedente): le inversioni restavano nei plot per `side` e nella descrizione dei cluster.

**Conseguenza ancora vera oggi**: `lesion_side_source = "clinical"` non indica più tutte le etichette del tsv. `src/pipeline/calibrate_lesion_side_threshold.py` usa quelle righe come verità, quindi non vede più le 11 inversioni: l'accordo che calcola ora è più alto del 97,4% (su 1445, inversioni incluse) della voce del 28-09-26 e non è confrontabile. Se la T1 mostrasse che sbaglia la maschera, la lista va svuotata e la run rifatta.

---

## 30-09-26 — Cache condivisa e ricampionamento single-pass per le mappe anatomiche in Embedding Explorer

**Decisione**: `BinaryMaskStore` (`src/analysis/anatomical_maps.py`) passa da precalcolo per-singola-run a cache in-memoria condivisa fra tutti i run/cluster aperti nella stessa sessione app: per ogni soggetto tiene solo gli indici dei voxel sopra soglia (lesione, o disconnessione >0.5), riempiti una sola volta per soggetto indipendentemente da quanti run/cluster lo richiedono. `_GridResampler`, stessa classe, calcola una sola volta la corrispondenza voxel→voxel fra griglia sorgente e reference (invece che per ogni soggetto) — bit-identico a `resample_to_img`, verificato con test dedicato. Nuovo flag `--preload` in `src/pipeline/embedding_app.py`: all'avvio, in background, legge tutti i soggetti di tutti i run di clustering (maschere lesionali sempre, disconnettomi SDC solo per i run sdc) e riempie i due store una volta per l'intera sessione. Inoltre, `_masked_for_view_colorbar` (`src/analysis/embedding_app.py`) rimuove il grigio dalla colorbar interattiva della mappa "probabilità media": pre-azzera i voxel sotto soglia (0.02) e passa un epsilon a `view_img` invece della soglia reale.

**Perché**: con un precalcolo per-singola-run, ogni cluster di ogni run ripeteva il ricampionamento e il filtraggio per voxel per gli stessi soggetti già visti in run precedenti nella stessa sessione — costo che cresce con il numero di run aperti, non con il numero di soggetti distinti. Condividere la cache per soggetto (indipendente dal run) elimina il lavoro ripetuto: con `--preload`, qualunque cluster di qualunque run mostra la mappa in ~1s. Sul colorbar: `view_img` di nilearn colora di grigio opaco tutto l'intervallo sotto soglia quando gli si passa la soglia reale, e questo comportamento non è configurabile dai suoi parametri pubblici — pre-azzerare a monte e passare un epsilon aggira il problema senza patch a nilearn.

**Alternative scartate**: mantenere il precalcolo per-run e limitarsi a velocizzare il ricampionamento (`_GridResampler` da solo) — avrebbe comunque ripetuto il lavoro per ogni run sullo stesso soggetto, non risolvendo il caso reale (più run aperti in una sessione lunga).

**Conseguenza ancora vera oggi**: i due store (`BinaryMaskStore` per lesioni e per disconnettomi SDC) vivono per la durata del processo `embedding_app`, non per singola run — un riavvio dell'app senza `--preload` torna al comportamento lazy (primo accesso più lento, poi cache calda per quel soggetto). Bug noto e non corretto: il download PNG statico della mappa di disconnessione (`_download_disconnection_png`) usa sempre `_DISCONNECTOME_DISPLAY_THRESHOLD` anche in modalità "percent", dove dovrebbe usare `1e-6` come la vista interattiva.

---

## 30-09-26 — Lista delle esclusioni con `scope`: un soggetto può essere inutilizzabile in una sola rappresentazione

**Decisione**: `assets/metadata/excluded_subjects.csv` ha una colonna in più, `scope` (vocabolario chiuso: `all`, `lesion`, `sdc-parcellated`, `sdc-voxelwise`, `sdc-streamline`), e un nuovo motivo `all_zero_features` (la riga di feature del soggetto è tutta zero nella rappresentazione dello scope). `load_excluded_subjects(path, scope)` restituisce le righe `all` più quelle del proprio scope; lo scope è un argomento obbligatorio, senza default. `build_lesion_matrix.py` chiede `lesion`, `build_sdc_matrix.py` chiede `sdc-<representation>`. Prima riga scritta: `sub-STUKLFR0671` (`empty_mask`, `all` — maschera a 0 voxel, vuoto ovunque) più 14 soggetti `all_zero_features` / `sdc-streamline`, cioè 15 escluse da `s2.3-stream` (5853 → 5838).

**Perché**: 14 soggetti hanno il CSV streamline interamente a zero mentre la loro mappa di disconnessione voxelwise non è vuota (10.498–214.149 voxel, lesioni fino a 284 voxel). Non è un difetto del calcolo: `streamline_ratio` conta le streamline effettivamente intersecate, e in quei soggetti la lesione tocca solo la frangia probabilistica dei tratti (probabilità massima dell'atlante 0,001–0,55, contro 0,997–1,000 nei soggetti con streamline non nullo). Sono misure vere ("nessuna streamline tagliata"), inutilizzabili nello spazio dei tratti perché una riga tutta zero è massimamente distante da tutte le altre, ma validi nella matrice lesionale e in quella voxelwise. Una lista globale li avrebbe fatti sparire da entrambe.

**Alternative scartate**: (a) una lista di esclusioni per pipeline — due file che divergono; (b) uno scope grossolano `lesion`/`sdc` — un'esclusione `sdc` toglierebbe i 14 anche da `s2.4-vol`, dove hanno disconnessione reale; (c) non escludere in fase di build e toglierli a valle nel notebook — sposta la decisione fuori dall'artefatto, che non dice più da solo chi contiene.

**Conseguenza ancora vera oggi**: la garanzia "le matrici lesione e SDC escludono gli stessi soggetti per costruzione" vale ora per le righe `all`; una riga con scope stretto restringe volutamente il confronto a un solo spazio di feature, e `config.md` di ogni matrice registra lo scope usato (`excluded_subjects_scope`). La validazione del file copre l'intero file, non solo le righe dello scope richiesto, così un refuso destinato a un'altra matrice fa fallire anche questa.

---

## 30-09-26 — Streamline per tratto come terza rappresentazione SDC, nella track s2.x

**Decisione**: `build_sdc_matrix.json` accetta `representation: "streamline"`, che legge `sdc/<subject>/*_LF-lesion_atlas-yeh_hcp1065_streamline.csv` (colonne `tract,streamline_ratio`) in una matrice soggetti x 87 tratti di sostanza bianca — un valore per tratto, la quota delle sue streamline colpite. Nuovo builder dedicato (`src.features.sdc.build_sdc_streamline_matrix`), non un parametro di quello parcellato. Lista autoritativa dei tratti in `assets/atlases/sdc_labels/yeh_hcp1065_streamline.csv` (colonna `tract`, 87 righe), derivata dall'unione su tutti i 1734 file reali. Il dato appartiene alla track **s2.x** (disconnettoma), non s1.x, nonostante il nome `LF-lesion`: quello che misura è una disconnessione, cioè streamline interrotte dalla lesione, non danno diretto al tessuto. Prima sessione: `s2.3-stream`, 7 dataset (UCL-UK non ha questo CSV).

**Perché un builder separato**: lo schema non ha nulla in comune con i CSV parcellati — nessuna colonna `region_name`, e una sola colonna di valori invece delle 6 statistiche interscambiabili di `KNOWN_VALUE_COLUMNS`. Di conseguenza la config non espone né `atlas` né `value_column` per questa modalità: non c'è niente da scegliere, e un campo non letto è vietato (`code_standards.md` §5).

**Perché un tratto mancante solleva invece di valere 0.0**: è l'unica differenza di comportamento reale rispetto al builder parcellato, che riempie a `0.0` perché BCBToolKit omette davvero le regioni a overlap nullo. Questo file invece scrive **tutti** i tratti, zeri compresi: verificato su tutti i 1734 file dei 7 dataset, stessi 87 tratti nello stesso ordine, da 2 a 42 non nulli per soggetto. Un file incompleto è quindi troncato o corrotto, e riempirlo sarebbe il fallback silenzioso che `code_standards.md` §0 esclude.

**Alternative scartate**: (a) generalizzare `build_sdc_matrix` con nomi di colonna configurabili — mette un parametro che non varia quasi mai sul percorso caldo della rappresentazione usata da ogni run esistente, senza guadagno; (b) un secondo file di config (`build_sdc_matrix_stream.json`) accanto a quello voxelwise — scartata su richiesta, si cambia `representation` nello stesso file; (c) trattarlo come atlante parcellato aggiungendone solo il file di reference — impossibile, manca `region_name`; (d) allineare per posizione di riga, dato che l'ordine è stabile su tutta la coorte — l'ordine non è garantito dal formato (`lessons_learned.md` #3), e dopo il controllo di completezza il `reindex` per nome non può comunque riempire niente, solo riordinare.

**Conseguenza ancora vera oggi**: nessuna colonna viene mai scartata, nemmeno se costante su tutti i soggetti ammessi — stessa regola del parcellato, la colonna `j` deve sempre indicare lo stesso tratto. Il clustering su questa matrice gira sui 87 tratti grezzi, senza dim reduction (`reduced_data: false`, `reduction_method: "raw"`): 87 dimensioni sono già basse, quindi `n_components` non entra in gioco.

## 29-09-26 — Esclusione dei soggetti: lista curata a mano al posto delle soglie in config

**Decisione**: `min_lesion_volume_voxels` e `max_out_of_brain_fraction` sono usciti da `build_lesion_matrix.json` (e da `BuildMatrixConfig`, `build_lesion_matrix()`, `_filter_by_lesion_quality`, ora cancellata). Chi escludere dalle matrici di produzione è deciso **a mano**, guardando le distribuzioni in `assets/metadata/lesion_metadata.csv` dal notebook `lesion_quality.ipynb`, e scritto in `assets/metadata/excluded_subjects.csv` (`subject_id, dataset, reason, value`; vocabolario chiuso dei motivi: `empty_mask`, `lesion_too_small`, `out_of_brain_fraction_too_high`). Quel file è letto sia da `build_lesion_matrix.py` sia da `build_sdc_matrix.py`, quindi le due matrici escludono gli stessi soggetti per costruzione.

**Perché**: i dati non hanno un salto naturale su cui mettere una soglia. Su 5853 soggetti: 3 maschere a 0 voxel a 2 mm, 132 con volume ≤ 10 voxel, e una coda continua senza discontinuità; il test IQR per dataset (log1p, Tukey 1.5) ne segnala solo 3, un quantile fisso al 2% ne prende 115. Sulla frazione fuori dal brain, 234 soggetti sopra il 5%, 73 sopra il 10%, 5 sopra il 30%. Una soglia in un config sceglie un numero arbitrario su quella coda e lo applica a tutti i dataset insieme; la decisione è invece caso per caso e appartiene all'analisi, non alla config di una pipeline. Il `value` per ogni riga tiene la decisione verificabile a distanza di mesi: "sub-X escluso" non si può rivedere, "sub-X escluso a 2 voxel" sì.

**Alternative scartate**: (a) tenere le soglie e affiancarci la lista — due meccanismi di ammissione attivi insieme, con il rischio che una soglia dimenticata in un config escluda soggetti che il notebook aveva deciso di tenere; (b) una lista per pipeline (una per la matrice lesionale, una per l'SDC) — due file che divergono, e un confronto lesione/SDC che silenziosamente confronta due coorti diverse; (c) far generare la lista da uno script a partire da soglie — sarebbe la soluzione (a) con un passaggio in più. Reintroduce `excluded_subjects`, scartata la mattina dello stesso giorno (vedi `project_changelog.md`, voce su `lesion_metrics`): allora l'argomento era che editare un config e rilanciare una pipeline di minuti fosse più macchinoso che correggere la cella a mano; ora la lista non fa rilanciare niente (è letta dalle pipeline di matrice, non da `enrich_metadata`) e la correzione a mano non è più possibile, perché ogni run di `enrich_metadata` ricopia le colonne derivate dalle maschere.

**Conseguenza ancora vera oggi**: un file assente **solleva**, non significa "non escludere nessuno" — le due cose sono indistinguibili, e costruire una matrice di produzione con tutti i soggetti limite dentro è esattamente ciò che la lista esiste per evitare. Per dire "nessuna esclusione" si tiene il file con la sola intestazione. Ogni riga è validata contro il registro (ID inesistente, ID duplicato, `dataset` in disaccordo, motivo non registrato, `value` non numerico sollevano): il file è scritto a mano e i dati ridondanti scritti a mano divergono. Oggi il file contiene solo l'intestazione: nessuna esclusione è ancora stata decisa.

---

## 29-09-26 — Metriche dalle maschere: quattro per griglia, su due griglie, con la correzione applicata prima del conteggio

**Decisione**: `assets/metadata/lesion_metadata.csv` registra, per ogni soggetto con maschera e **per ogni griglia dichiarata**, quattro valori: `lesion_volume_voxels_<g>`, `out_of_brain_fraction_<g>`, `laterality_index_<g>`, `lesion_side_<g>`. Le griglie in produzione sono due, `1mm` e `2mm`. Ordine di calcolo per ogni maschera e ogni griglia: ricampiona se e solo se la griglia della maschera differisce, binarizza, **misura la frazione fuori dal brain sulla maschera grezza**, azzera i voxel fuori dal brain (`correct_out_of_brain: true`), poi conta volume e lateralità. Un solo passaggio: una lettura da disco per soggetto, un ricampionamento per griglia.

**Perché due griglie**: le maschere manuali sono tutte a 1 mm (verificato sugli header di tutte e 5853: `182x218x182`, voxel `1.0`), il template di produzione è a 2 mm con ricampionamento `nearest`, che tiene un voxel su 8. Il conteggio a 2 mm è quindi un sottocampionamento in cui una lesione minuscola può ridursi o sparire; a 1 mm è nativo ed esatto. Confrontare i due volumi è l'unico modo per dire se una maschera a 0 voxel a 2 mm (3 soggetti: `sub-STUKLFR0671`, `sub-STUKE0146`, `sub-STUKE0201`) sia vuota nel file originale o abbia perso la lesione nel ricampionamento.

**Perché la frazione è pre-correzione e il resto post**: la correzione porta la frazione a 0 per costruzione, quindi misurarla dopo renderebbe inutile la sola colonna che serve a decidere chi escludere. Viceversa un voxel fuori dal cervello non è lesione: non va contato nel volume e non deve poter decidere il lato. Verificato che il caso è reale: senza correzione, 3 voxel di destra fuori dal brain contro 2 di sinistra dentro danno indice −0.2 e lato `right`; con la correzione, +1.0 e `left`.

**Alternative scartate**: contare senza correzione (contare voxel fuori dal cervello non ha senso, e il volume divergerebbe da quello di una matrice costruita con `correct_out_of_brain: true`); il lato solo sulla griglia a 2 mm, quella su cui la soglia è calibrata (a 1 mm il conteggio è esatto, quindi è la griglia *migliore* per attribuire il lato, non la peggiore — tenerle entrambe permette di ricalibrare senza rileggere le maschere); salvare il volume in mm³ (indipendente dalla griglia ma non risolve la perdita per sottocampionamento).

**Verificato dopo la prima run completa (30-09-26)**: per 5150 dei 5853 soggetti la griglia a 1 mm **non porta informazione in più**. `manual_masks/` contiene la lesione già ricampionata da BCBToolKit su griglia 1 mm (`docs/dev/retrieval.md`), e per i dataset segmentati originariamente a 2 mm i voxel risultano costanti in blocchi 2x2x2 allineati (fase `(1,1,1)`, zero blocchi misti, verificato su tutti i soggetti): UCL-UK, UKLFR, WashU, NEMESIS_T0, SFB936. Il conteggio a 2 mm ricostruisce esattamente la maschera nativa, quindi per loro nessuna lesione può sparire nel sottocampionamento. Le due colonne differiscono davvero solo per i 702 soggetti di PASPORT, PSP e WAKEUP. **Il disegno resta giustificato**: dei 4 soggetti con volume 0 sulla griglia di produzione, solo `sub-STUKLFR0671` ha la maschera davvero vuota; `sub-STUKE0146` (8 voxel) e `sub-STUKE0201` (3 voxel) hanno una lesione reale persa a 2 mm, ed entrambi stanno in WAKEUP, cioè fra i 702. Il quarto, `sub-STUNIPD0558`, arriva a 0 per la correzione (99,94% di lesione fuori dal cervello), non per la risoluzione. La ridondanza cade quindi esattamente dove è inevitabile, e l'informazione dove serve.

**Conseguenza ancora vera oggi**: `side_threshold=0.20` è calibrata **solo sulla griglia a 2 mm** (97.4% di accordo su 1445 soggetti, voce del 28-09-26) e viene applicata anche a 1 mm, dove non è verificata: `lesion_side_1mm` è indicativa finché `scripts/calibrate_lesion_side_threshold.py --grid 1mm` non viene eseguito. Il piano mediano escluso da entrambi gli emisferi è spesso 1 mm su una griglia e 2 mm sull'altra (la griglia a 1 mm ha 91 fette a sinistra e 90 a destra, quella a 2 mm 45 e 45), quindi per una lesione quasi tutta mediana i due indici non sono interscambiabili. `out_of_brain_fraction` è `NaN`, non `0.0`, per una maschera vuota: 0.0 metterebbe una maschera vuota tra i soggetti più puliti della distribuzione usata per scegliere le esclusioni. Nel registro `participants.csv` arrivano solo `lesion_volume_voxels_2mm` e `lesion_side`: il volume a 1 mm, le due frazioni e i due indici vivono solo nel csv, che è quello che legge il notebook.

---

## 29-09-26 — `correct_out_of_brain`: correggere (azzerare i voxel) invece di escludere il soggetto

**Decisione**: `build_lesion_matrix.json`/`BuildMatrixConfig` guadagna `correct_out_of_brain` (bool, default `false`) — invece di escludere un soggetto contaminato (`max_out_of_brain_fraction`), azzera i suoi voxel di lesione fuori dalla maschera cerebrale (`src/features/lesion_correction.py::zero_out_of_brain_voxels`) e lo mantiene nella matrice, con `lesion_volume_voxels` ricalcolato dai dati corretti. Applicato in `src/features/lesion.py::_apply_out_of_brain_correction`, eseguito **prima** di `min_lesion_volume_voxels` così quel filtro vede il volume già corretto, non quello grezzo. **Mutuamente esclusivo con `max_out_of_brain_fraction`**: entrambi attivi sollevano `ValueError`, sia a config-load (`src/analysis/build_config.py`) sia dentro `build_lesion_matrix` stesso (`lessons_learned.md` #2, validazione non ancorata a un solo punto di chiamata).

**Perché**: combinare le due strategie sullo stesso soggetto sarebbe ambiguo — se si corregge prima e si esclude dopo, la soglia `max_out_of_brain_fraction` controllerebbe una frazione già portata a ~0 dalla correzione, diventando silenziosamente inutile; se si esclude prima sulla frazione grezza, la correzione non avrebbe più nulla da fare sui sopravvissuti in caso di soglie strette. Richiesto esplicitamente dall'utente come alternativa all'esclusione pura introdotta nella voce del 28-09-26 in questo stesso file.

**Alternativa scartata**: combinare i due meccanismi (esclusione sulla frazione grezza + correzione sui sopravvissuti). Scartata su richiesta esplicita dell'utente per restare più semplice e priva di ambiguità — un solo criterio di ammissione attivo alla volta, mai due che interagiscono implicitamente.

**Conseguenza ancora vera oggi**: `config/pipelines/build_lesion_matrix.json` ha `correct_out_of_brain: false` — comportamento di produzione invariato, nessuna matrice già costruita è affetta (i thresholds/la correzione contano solo per run non ancora fatte, stessa nota della voce del 28-09-26). Il vecchio script standalone `scripts/lesion_fix.py`, che faceva la stessa correzione ma non era mai integrato in nessuna pipeline, è stato eliminato in questa stessa sessione (vedi `project_changelog.md`).

**Aggiornamento, stessa giornata**: la mutua esclusione descritta sopra **non esiste più**, perché `max_out_of_brain_fraction` è stata rimossa del tutto (voce "Esclusione dei soggetti: lista curata a mano", in cima a questo file). `correct_out_of_brain` resta, come unico uso di `brain_mask_path` in `build_lesion_matrix.json`, ed è attiva anche in `compute_lesion_metadata.json` (lì `true`). La ragione per cui le due strategie non andavano combinate resta valida e spiega perché non è stata tenuta una soglia accanto alla lista.

---

## 28-09-26 — `lesion_side` geometrico: soglia di bilateralità 0.20, dal protocollo standard di letteratura

**Decisione**: implementato il fallback geometrico per `lesion_side` (per i soggetti privi di dato clinico), con soglia di bilateralità **0.20** sul laterality index `LI = (left_voxels - right_voxels) / (left_voxels + right_voxels)` — la formula/soglia standard in letteratura per lesioni/attivazione fMRI (LI-toolbox di Wilke & Lidzba; protocollo Rorden/GigaScience per lesioni stroke), non calcolata da zero per questo progetto.

**Perché**: prima di questa sessione la variabile era esplicitamente non implementata (`docs/dev/metadata.md`), in attesa di una calibrazione della soglia contro dati clinici veri (`code_standards.md` §0 — mai un valore "dall'aria plausibile"). Calibrazione eseguita (`scripts/calibrate_lesion_side_threshold.py`) su 1445 soggetti con `lesion_side` clinico nei 5 dataset che lo hanno (`UNIPD/WashU`, `UNIPD/PSP`, `UKLFR/stroke_UKLFR`, `UKE/WAKEUP_acute`, `UKE/SFB936_ses01` - quest'ultimo onboardato nella stessa sessione, portando il set di calibrazione da 4 a 5 dataset): 0.20 riproduce il 97.4% delle etichette vere. Dettagli completi, matrice di confusione e letteratura in `knowledge/neuroimaging/lesion_laterality.md`.

**Alternativa scartata**: la soglia "ottimale" trovata per grid search sui nostri dati (0.36, accuratezza 97.5%, +2 soggetti su 1445 rispetto a 0.20). Scartata perché il guadagno è marginale e rischierebbe di overfittare sui soli 24 esempi di `both` (la classe bilaterale) disponibili nel set di calibrazione — usare il valore di letteratura resta anche più difendibile in caso di pubblicazione.

**Conseguenza ancora vera oggi**: la classe `both` resta debole a qualunque soglia testata (3/24 corretti anche alla soglia ottimale) - non un difetto della soglia scelta, un limite intrinseco del metodo per una lesione bilaterale che comunque pende leggermente da un lato nel conteggio voxel. `UNIPD/NEMESIS_T0` (onboardato lo stesso giorno, nessun `lesion_side` clinico) non riceve ancora il fallback: `build_lesion_matrix.json` non include questo dataset nella propria lista `datasets` (stesso gap già noto per `lesion_volume_voxels`, task separato non ancora fatto) - il fallback lo salta con un `WARNING`, non un errore, finché quella lista non viene estesa.

---

## 28-09-26 — `build_lesion_matrix.json` riportato alla griglia a 2mm, era scivolato a 1mm

**Decisione**: `reference_template_path`/`brain_mask_path` in `config/pipelines/build_lesion_matrix.json` passati da `tpl-MNI152NLin6Asym_res-1_*` (1mm) a `tpl-MNI152NLin6Asym_res-2_*` (2mm). Aggiornati anche i due path hardcoded nella sezione "Lesione fuori dal brain" di `notebooks/exploration/dataset_exploration.ipynb`, per restare sulla stessa griglia della produzione.

**Perché**: la voce del 06-09-26 in questo stesso file fissa la griglia a 2mm per `build_lesion_matrix.py` (e per `build_sdc_matrix.py` in modalità `voxelwise`), con alternative misurate e scartate esplicitamente. Lo swap del 23-09-26 da un singolo file paziente a un template versionato (`project_changelog.md`) ha però impostato `res-1` (1mm) — non una scelta di risoluzione deliberata, solo la prima opzione disponibile al momento di rendere il riferimento stabile — introducendo una deviazione silenziosa dalla griglia già decisa. Richiesto esplicitamente dall'utente ("voglio risoluzione a 2mm"), verificato prima di applicare che `res-2` T1w e brain mask condividano shape/affine (91×109×91, 2mm isotropo).

**Conseguenza ancora vera oggi**: `config/pipelines/build_sdc_matrix.json` (rappresentazione `voxelwise`) ha la **stessa** deviazione — `reference_template_path` è ancora su `res-1` — e non è stato toccato in questa sessione (fuori scope, riguarda solo `build_lesion_matrix.json`). Da allineare quando si torna a lavorare su quella pipeline. Nessun impatto su matrici già costruite (`data/derived/lesion_matrix/<sessione>/`): la griglia è fissata al momento del build, questo è solo un cambio di config per le run future.

---

## 28-09-26 — Filtro di qualità della lesione (volume minimo, frazione fuori dal brain): solo per `build_lesion_matrix.py`, non per `build_sdc_matrix.py`

**Decisione**: `build_lesion_matrix.py` guadagna due soglie opzionali di ammissione soggetto, entrambe `null` di default (nessun filtro): `min_lesion_volume_voxels` (esclude lesioni troppo piccole) e `max_out_of_brain_fraction` (esclude soggetti con troppi voxel di lesione fuori dalla maschera cerebrale MNI152, stessa logica di `scripts/lesion_fix.py`, richiede `brain_mask_path`). Entrambe calcolate in-run, dai dati voxel già caricati/binarizzati di quella specifica run (`src/features/lesion.py::_filter_by_lesion_quality`), non da `assets/metadata/participants.csv` — la cui colonna `lesion_volume_voxels` potrebbe riflettere una griglia/`binarize_threshold` di una run diversa. Un soggetto a 0 voxel di lesione ottiene `out_of_brain_fraction = 0.0` per convenzione esplicita (vacuosamente vero), mai `NaN`. I soggetti esclusi sono elencati in due nuove sezioni di `config.md`/`summaries/build_lesion_matrix/*/build_summary__*.md` ("Excluded by min_lesion_volume_voxels"/"Excluded by max_out_of_brain_fraction"), stesso schema già in uso per `group_filter`.

**Alternativa scartata**: implementare lo stesso meccanismo anche in `build_sdc_matrix.py`/`src/features/sdc.py`, come inizialmente richiesto. Scartata perché `sdc.py` risolve deliberatamente la presenza della lesion mask da `assets/metadata/participants.csv` (`has_lesion`), mai da un glob su `manual_masks/` — scelta presa apposta dopo un bug reale (debug 27-08-26, vedi `docs/dev/sdc_matrix.md` §"Why participants.tsv, not manual_masks/ on disk": una copia locale parziale dei dati falsava l'ammissione). Aggiungere qui le due soglie avrebbe richiesto o ricaricare `manual_masks/` direttamente (reintroducendo esattamente quel rischio) o precalcolare le metriche in `participants.csv` (un nuovo componente pipeline, fuori scope). Interpellato esplicitamente, l'utente ha confermato che le due soglie derivano dalla lesione e servono solo a `lesion_matrix`.

**Conseguenza ancora vera oggi**: una matrice già costruita in `data/derived/lesion_matrix/<sessione>/` non viene mai filtrata a posteriori — cambiare il criterio di ammissione non ha alcun effetto su un output già scritto. Se ci si accorge di aver dimenticato un'esclusione, la run va cancellata (cartella di output + riga in `runs.csv`) e rifatta da capo, mai patchata in-place.

**Superseduta il 29-09-26, stessa giornata**: le due soglie non esistono più, sostituite da una lista di soggetti curata a mano (voce in cima a questo file). L'alternativa scartata qui sopra — portare lo stesso meccanismo in `build_sdc_matrix.py` — è invece stata realizzata nella nuova forma, e per il motivo opposto a quello che allora la bloccava: una lista di `subject_id` non richiede a `sdc.py` di caricare nessuna maschera, quindi non reintroduce il rischio del glob su `manual_masks/`.

---

## 07-09-26 — Clustering lesionale: nessun k unico di produzione, per scelta

**Decisione**: per s1.1-vol e s1.2-vol non viene eletto un k di produzione. Le opzioni prodotte (k=4/5/6 su più metodi, più le varianti hdbscan e, su s1.1-vol, spectral a k=8) restano tutte valide in parallelo, ognuna come una lettura diversa della stessa struttura. Scritta nelle sezioni `Decisioni` di `docs/experiments/clustering/s1_production.md`, che erano rimaste vuote.

**Perché**: nessun criterio interno converge su un k solo — la silhouette premia k alti per costruzione, CH cresce quasi sempre con k, l'inertia non ha un gomito netto (`s1_tuning.md`). Restringere a un valore significherebbe delegare a una metrica di comodo una scelta che quella metrica non sa fare. In più il k non è separabile da `n_components` dell'embedding: il k migliore non converge tra n2/n3/n10, quindi i due vanno decisi insieme, a valle.

**Alternativa scartata**: eleggere un k unico su una metrica interna (tipicamente il massimo di silhouette). Scartata perché produrrebbe una scelta apparentemente oggettiva ma guidata da un artefatto della metrica, non dalla struttura dei dati.

**Conseguenza ancora vera oggi**: il confronto tra opzioni avviene in `notebooks/post-results_analysis/clustering_evaluation.ipynb`, che ne carica un sottoinsieme alla volta in `SELECTED_RUNS`. Una run di produzione presente in `results/` non è quindi "la" scelta: è una delle opzioni tenute aperte apposta.

---

## 06-09-26 — Ricampionamento a 2mm con `nearest`: confermato, alternative misurate

**Decisione**: ogni matrice voxel-wise resta sulla griglia MNI152NLin6Asym a 2mm con `resample_interpolation: "nearest"`. Vale per `build_lesion_matrix.py` e per `build_sdc_matrix.py` in modalità `voxelwise`.

**Contesto**: 2 soggetti UKE sono entrati in `lesion_matrix` s1.3-vol come righe tutte-zero (voce del 06-09-26 in `data_changelog.md`), il che ha aperto la domanda se `nearest` fosse la scelta sbagliata per tutte le run future.

**Misurato prima di decidere** (griglie native: UCL-UK e WashU già a 2mm, UKLFR a 1.5mm, PASPORT/PSP/UKE a 1mm — 1399 soggetti su 5720 vengono effettivamente ricampionati):

| | bias sul volume totale | errore mediano per soggetto | lesioni azzerate (48 più piccole) |
|---|---:|---:|---:|
| `nearest` | −1,5% | 1,6% | 2 |
| `linear` | −1,6% | 1,8% | 2 |

**Alternative scartate:**

- **`linear`**: misurata equivalente, e marginalmente peggiore in aggregato. Azzera *esattamente le stesse* 2 lesioni. Il motivo è che `nilearn.image.resample_to_img` con `linear` interpola tra i vicini del punto campionato, non media il blocco di 8 voxel: in downsampling si comporta quasi come `nearest`. E anche una media vera non salverebbe una lesione da 3 voxel, che resta sotto `binarize_threshold` 0.5 (3/8 = 0,375).
- **`continuous`**: già esclusa in precedenza per un motivo indipendente — lascia rumore di arrotondamento (~1e-17) attorno allo zero che impedisce a `_drop_constant_features` di scartare i voxel costanti.
- **Griglia a 1mm**: scartata per due ragioni. Una matrice SDC voxel-wise su ~1570 soggetti a 1mm sarebbe dell'ordine delle decine di GB (7,2M voxel per soggetto), non trattabile in locale; e la griglia comune a 2mm tiene la matrice lesionale e quella SDC allineate voxel per voxel, che è il presupposto della rappresentazione multimodale.

**Conseguenza ancora vera oggi**: la perdita non dipende dalla dimensione della lesione ma da *dove cade rispetto alla griglia* — nei dati misurati una lesione da 15 mm³ sopravvive e una da 16 mm³ sparisce. Non esiste quindi una soglia di volume sotto la quale "si sa" che il soggetto verrà perso: va controllato il volume post-ricampionamento, non quello nativo.

**Deciso di non intervenire sul codice** (07-09-26): `build_lesion_matrix.py` continua ad ammettere una riga tutta-zero senza segnalarla, a differenza di `build_sdc_matrix.py` che per il rischio equivalente esclude esplicitamente e traccia l'esclusione. Valutato non proporzionato: 2 soggetti su 5720 (0,035%). I due casi noti restano in `06-09_s1.3-vol` e sono documentati in `docs/experiments/processing/matrices.md`; chi userà quella matrice li filtra a valle se gli serve. Da rivedere se un dataset futuro ne producesse un numero non trascurabile — il segnale da guardare è il volume minimo *dopo* il ricampionamento, non quello nativo.

---

## 27-08-26 — Ammissione soggetti in `build_sdc_matrix.py`: controllo su `participants.csv`, non su `manual_masks/` su disco

**Decisione**: l'ammissione di un soggetto alla matrice SDC controlla `has_lesion` nel registro (`assets/metadata/participants.csv`), non l'esistenza del file su `manual_masks/` in locale.

**Perché**: su questa macchina locale `manual_masks/` conteneva solo un campione di 10 soggetti per dataset, mentre `sdc/` era già completo — un controllo sul disco locale ammetteva solo 40/1151 soggetti, escludendo erroneamente soggetti con una lesion mask reale ma non ancora retrievata localmente.

**Alternativa scartata**: controllare `manual_masks/` su disco direttamente — inaffidabile perché un retrieval locale parziale non riflette la disponibilità reale dei dati alla fonte.

**Conseguenza ancora vera oggi**: con il criterio sul registro, la run reale di allora ammetteva 1119/1151 soggetti; i 32 esclusi erano confermati genuinamente assenti dal registro clinico, non un artefatto di retrieval locale. La regola corrente (controllo su registro, non su disco) è documentata in `docs/guides/sdc_matrix_building.md`/`docs/dev/sdc_matrix.md`.

---

## 25-08-26 — `build_lesion_matrix.py`: rimossa la modalità `parcellated`

**Decisione**: `build_lesion_matrix.py` produce solo matrici voxel-wise; la modalità `parcellated` (matrice per macro-aree anatomiche via atlante) è stata rimossa dalla pipeline.

**Perché/dettagli**: vedi `management/notes/TODO.md`.

**Conseguenza ancora vera oggi**: non esiste un parametro di rappresentazione per questa pipeline — la matrice lesionale prodotta è sempre voxel-wise (a differenza di `build_sdc_matrix.py`, che ha sia `parcellated` sia `voxelwise`).
