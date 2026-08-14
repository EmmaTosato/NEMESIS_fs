### L ow -dimensional embeddings of high -dimensional data

Cyril de Bodt 1 , 2 ,* , Alex Diaz-Papkovich 3 ,* , Michael Bleher 4 , Kerstin Bunte 5 , Corinna Coupette 6 , 7 , 8 , Sebastian Damrich 9 , Enrique Fita Sanmartin 10 , 11 , Fred A. Hamprecht 12 , Em˝ oke- ´ Agnes Horv´ at 13 , Dhruv Kohli 14 , Smita Krishnaswamy 15 , John A. Lee 2 , Boudewijn P. F. Lelieveldt 16 , Leland McInnes 17 , Ian T. Nabney 18 , Maximilian Noichl 19 , Pavlin G. Poliˇ car 20 , Bastian Rieck 21 , Guy Wolf 10 , 11 , Gal Mishne 14 ,+ , and Dmitry Kobak 9 ,+

* Equal contribution

> + Equal contribution

1 Department of Mathematics and Namur Research Institute for Complex Systems (naXys), University of Namur, Belgium 2 ICTEAM Institute, UCLouvain, Louvain-la-Neuve, Belgium 3 Data Science Institute, Brown University, Providence, Rhode Island, United States 4 Institute for Mathematics, Heidelberg University, Germany 5 University of Groningen, The Netherlands 6 Aalto University, Finland 7 Max Planck Institute for Informatics, Saarbr¨ ucken, Germany 8 Max Planck Institute for Tax Law and Public Finance, Munich, Germany 9 Hertie Institute for AI in Brain Health, University of T¨ ubingen, Germany 10 Universit´ e de Montr´ eal, Canada 11 Mila, Montr´ eal, Canada 12 IWR, Heidelberg University, Germany 13 Northwestern University, Evanston, Illinois, United States 14 UC San Diego, California, United States 15 Yale University, New Haven, Connecticut, United States 16 Department of Radiology, Leiden University Medical Center, The Netherlands 17 Tutte Institute for Mathematics and Computing, Ottawa, Canada 18 University of Bristol, United Kingdom

19 Department of Philosophy and Religious Studies, Utrecht University, The Netherlands 20 Faculty of Computer and Information Science, University of Ljubljana, Slovenia 21 University of Fribourg, Switzerland

/a0 dmitry.kobak@uni-tuebingen.de

August 25 ,

2025

### Abstract

Large collections of high-dimensional data have become nearly ubiquitous across many academic fields and application domains, ranging from biology to the humanities. Since working directly with high-dimensional data poses challenges, the demand for algorithms that create low-dimensional representations, or embeddings , for data visualization, exploration, and analysis is now greater than ever. In recent years, numerous embedding algorithms have been developed, and their usage has become widespread in research and industry. This surge of interest has resulted in a large and fragmented research field that faces technical challenges alongside fundamental debates, and it has left practitioners without clear guidance on how to effectively employ existing methods. Aiming to increase coherence and facilitate future work, in this review we provide a detailed and critical overview of recent developments, derive a list of best practices for creating and using low-dimensional embeddings, evaluate popular approaches on a variety of datasets, and discuss the remaining challenges and open problems in the field.

