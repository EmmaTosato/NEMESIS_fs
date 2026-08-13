# Metodi di riduzione della dimensionalità — riepilogo

> Fonte: de Bodt, Diaz-Papkovich, Kobak et al. 2025, "Low-dimensional embeddings of high-dimensional data" (review Dagstuhl seminar 24122).

## Idea di base
Dati con molte feature (D dimensioni) → rappresentazione in poche dimensioni (d ≪ D), sacrificando informazione. Ogni metodo sceglie **cosa preservare**: varianza, distanze globali, vicini locali, struttura del manifold.

---

## 1. Metodi lineari
| Metodo | Cosa preserva | Note |
|---|---|---|
| **PCA** | Varianza / errore di ricostruzione | Proiezione su assi ortogonali; interpretabile; nessun numero di componenti "tipico" assunto qui — si sceglie guardando la varianza cumulativa spiegata, caso per caso (vedi `docs/knowledge/dim_reduction.md`) |
| **ICA** | Componenti indipendenti (non solo non correlate) | Usata per blind source separation (es. EEG) |

## 2. Metodi basati su distanze
| Metodo | Cosa preserva | Note |
|---|---|---|
| **MDS (metric/classical/non-metric)** | Tutte le distanze a coppie | Classical MDS = equivalente a PCA su distanze euclidee; soffre di *norm concentration* in alta dimensione |
| **Sammon's mapping, CCA** | Distanze piccole (pesate) | Danno priorità ai vicini rispetto alla struttura globale |

## 3. Metodi probabilistici
| Metodo | Cosa preserva | Note |
|---|---|---|
| **Probabilistic PCA / Factor Analysis** | Verosimiglianza di un modello a variabili latenti | Usati per interpretare fattori nascosti (es. psicometria), non tanto per visualizzare |
| **GTM** | Come sopra, non lineare | Griglia regolare nello spazio latente |

## 4. Metodi spettrali (basati su grafo k-NN, assunzione di manifold)
| Metodo | Cosa preserva | Note |
|---|---|---|
| **Laplacian Eigenmaps** | Relazioni di vicinato nel grafo | Eigendecomposizione del Laplaciano normalizzato |
| **Diffusion Maps** | Distanze di diffusione (random walk sul grafo) | Può essere reso invariante alla densità di campionamento |
| **LLE** | Ricostruzione lineare locale dai vicini | — |
| **Isomap** | Distanze geodetiche sul grafo (MDS classica su queste) | Buono per manifold lisce; sensibile a "shortcut" nel grafo/rumore |
| **PHATE** | Distanze di potenziale (variante diffusion) | Più robusto di Isomap; pensato per strutture continue (es. traiettorie cellulari) |

## 5. Metodi neighbor-embedding (i più usati oggi per visualizzare cluster)
| Metodo | Cosa preserva | Note |
|---|---|---|
| **t-SNE** | Solo i vicini più prossimi (non le distanze globali) | Meno sensibile a shortcut nel grafo; produce cluster ben separati; riferimento: **Thiebaut de Schotten 2020** |
| **UMAP** | Vicini più prossimi, con attrazione più forte di t-SNE | Cluster più compatti; scalabile; nessun numero di componenti assunto qui — vedi `docs/knowledge/dim_reduction.md`, sezione "UMAP e clustering: quante componenti?" per la verifica completa (Talozzi 2023 usa 2D, **non** un precedente per componenti >2) |

**Importante**: in entrambi (t-SNE, UMAP) le **distanze tra cluster** nell'embedding **non sono affidabili** — solo l'appartenenza/vicinanza locale lo è.

---

## Trade-off generale
- **PCA / MDS** → buona struttura **globale**, dettagli locali persi
- **t-SNE / UMAP** → ottimi per **cluster locali**, struttura globale/distanze tra cluster non interpretabile
- **Isomap / PHATE / Laplacian Eigenmaps** → compromesso, indicati per strutture **continue** (non solo cluster discreti)

**Best practice del paper** (de Bodt, Diaz-Papkovich, Kobak et al. 2025, arXiv:2508.15929, §5 — verificato sul testo completo, non solo sull'abstract): non fidarsi di un solo metodo — confrontare più embedding sullo stesso dataset (come usare microscopi diversi sullo stesso campione); *"2D embeddings are not suited for downstream computational analysis, as they can introduce distortions and artifacts that will be picked up downstream. It is usually more appropriate to perform regression, classification, or clustering on higher-dimensional data, and only use 2D embeddings for exploration and communication."* — **nessun numero di componenti "giusto" assunto qui per il clustering**: quanto serve dipende dal metodo e dal caso, va deciso volta per volta (non un default fisso, es. non "5-10D per ogni metodo"). L'unica cifra concreta che il paper riporta (5–10D, §3.5/§6.1) è specifica a UMAP, non generalizzata a t-SNE — vedi la riga UMAP sopra, ancora da rivedere separatamente per l'attribuzione corretta.

---

## Applicazione a NEMESIS — Task 1 (clustering lesioni, ~4000–5800 pazienti)
- Obiettivo: separazione netta dei cluster topografici → **t-SNE/UMAP** più adatti di PCA/MDS
- **UMAP** preferito per N grandi: 2D per visualizzazione; per componenti >2 come input al clustering, nessun default assunto — vedi `docs/knowledge/dim_reduction.md`
- Attribuzione citazioni: **t-SNE → Thiebaut de Schotten 2020** (2D). UMAP nel progetto non ha un precedente diretto in letteratura per componenti >2 (Talozzi 2023 usa 2D — vedi sopra)
- Caveat da mantenere: le distanze inter-cluster nell'embedding non vanno interpretate come significative
