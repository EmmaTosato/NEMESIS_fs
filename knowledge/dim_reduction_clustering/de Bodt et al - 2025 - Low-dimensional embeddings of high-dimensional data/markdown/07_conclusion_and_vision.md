## 7 Conclusion and vision

Today, researchers live in a world where their capacity to access or produce data often exceeds their ability to understand it. Since much of this data is high-dimensional, machine-learning methods that produce low-dimensional embeddings have gained importance in exploratory data analysis. In this paper, we argued that low-dimensional embeddings and visualizations can guide analyses and discussions, highlight interesting patterns, and yield new hypotheses, investigations, or questions. By creating compelling figures and adding transparency to the scientific process, embeddings also play an important role in research communication. Paraphrasing George Box (Box, 1979 ): All embeddings are wrong, but some are useful.

As data availability continues to improve, we anticipate an increased interest in low-dimensional embedding methods across various data-intensive disciplines. This includes not only machine learning and biotechnology, but also interdisciplinary fields like digital humanities and computational social science. The continued cross-pollination between methods and applications across such widely different domains promises exciting methodological developments for the field. Research on low-dimensional embeddings has already made tremendous progress (compare Figure 1 with Figure 3 ), and we expect further advances in the oncoming years.

However, as we emphasized throughout the paper, embedding methods often involve technical complexities that may not be immediately apparent to their users. Making these methods accessible to interdisciplinary researchers requires promoting awareness of best practices and methodological limitations. It also requires addressing the many remaining algorithmic and interpretational challenges identified above. Overall, embedding methods hold strong potential to shape the future of data-driven research.

### Acknowledgments

This work was conceived at the Dagstuhl seminar 24122 supported by the Leibniz Center for Informatics. CdB conducted part of this work while being a beneficiary of an FSR Incoming Post-doctoral Fellowship from UCLouvain. ADP is supported by National Institutes of Health (NIH) Grant R 35 GM 139628 . MB is funded by the Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) under Germany's Excellence Strategy EXC 2181 / 1 -390900948 (the Heidelberg STRUCTURES Excellence Cluster). KB is supported by the Netherlands Organisation for Scientific Research (NWO) under Vidi grant number VI.Vidi. 193 . 098 . CC conducted part of this work while supported by Digital Futures at KTH Royal Institute of Technology. SD is supported by the German Ministry of Science and Education (BMBF) via the T¨ ubingen AI Center ( 01 IS 18039 ) and by the National Institutes of Health (UM 1 MH 130981 ). SD and DK are supported by the Gemeinn¨ utzige Hertie-Stiftung. E ´ AH is supported by the National Science Foundation (NSF CAREER Grant IIS1943506 ). JAL is a research director with the Belgian F.R.S.-FNRS (Fonds National de la Recherche Scientifique). BR acknowledges that this work has received funding from the Swiss State Secretariat for Education, Research and Innovation (SERI). GW is supported by a Humboldt Research Fellowship, CIFAR AI Chair, and NSERC Discovery grant 03267 . GMis partially supported by the National Science Foundation grants CCF2217058 and EFRI BRAID 2223822 . DK is a member of the Germany's Excellence cluster 2064 'Machine Learning New Perspectives for Science' (EXC 390727645 ). The content provided here is solely the responsibility of the authors and does not necessarily represent the official views of the funding agencies.

### References

Charu C Aggarwal, Alexander Hinneburg, and Daniel A Keim. On the surprising behavior of distance metrics in high dimensional space. In International Conference on Database Theory , pages 420 -434 , 2001 .

- Ehsan Amid and Manfred K Warmuth. TriMap: Largescale dimensionality reduction using triplets. arXiv , 2019 .
- Philipp Angerer, Laleh Haghverdi, Maren B¨ uttner, Fabian J Theis, Carsten Marr, and Florian Buettner. destiny: diffusion maps for large-scale single-cell data in r. Bioinformatics , 32 ( 8 ): 1241 -1243 , 2016 .

Francis J Anscombe. Graphs in statistical analysis. The American Statistician , 27 ( 1 ): 17 -21 , 1973 .

George Armstrong, Gibraan Rahman, Cameron Martino, Daniel McDonald, Antonio Gonzalez, Gal Mishne, and Rob Knight. Applications and comparison of dimensionality reduction methods for microbiome data. Frontiers in Bioinformatics , 2 , 2022 .

Sanjeev Arora, Wei Hu, and Pravesh K Kothari. An analysis of the t-SNE algorithm for data visualization. In Conference on Learning Theory , pages 1455 -1462 , 2018 .

Aleksandr Artemenkov and Maxim Panov. NCVis: noise contrastive approach for scalable visualization. In The Web Conference , pages 2941 -2947 , 2020 .

Micha¨ el Aupetit. Visualizing distortions and recovering topology in continuous projection techniques. Neurocomputing , 70 ( 7 ): 1304 -1330 , 2007 .

- Etienne Becht, Leland McInnes, John Healy, CharlesAntoine Dutertre, Immanuel WH Kwok, Lai Guan Ng, Florent Ginhoux, and Evan W Newell. Dimensionality reduction for visualizing single-cell data using UMAP. Nature Biotechnology , 37 ( 1 ): 38 -44 , 2019 .
- Mikhail Belkin and Partha Niyogi. Laplacian eigenmaps and spectral techniques for embedding and clustering. In Advances in Neural Information Processing Systems , pages 585 -591 , 2002 .
- Mikhail Belkin and Partha Niyogi. Convergence of Laplacian eigenmaps. In Advances in Neural Information Processing Systems , volume 19 , 2006 .
- B´ arbara C Benato, Alexandre X Falc˜ ao, and Alexandru C Telea. Measuring the quality of projections of highdimensional labeled data. Computers & Graphics , 116 : 287 -297 , 2023 .
- Yoshua Bengio, Olivier Delalleau, Nicolas Le Roux, JeanFranc ¸ois Paiement, Pascal Vincent, and Marie Ouimet. Learning eigenfunctions links spectral embedding and kernel PCA. Neural Computation , 16 ( 10 ): 2197 -2219 , 2004 .
- Hadas Benisty, Daniel Barson, Andrew H Moberly, Sweyta Lohani, Lan Tang, Ronald R Coifman, Michael C Crair, Gal Mishne, Jessica A Cardin, and Michael J Higley. Rapid fluctuations in functional connectivity of cortical networks encode spontaneous behavior. Nature Neuroscience , 27 ( 1 ): 148 -158 , 2024 .
- Adrien Bibal and Benoit Fr´ enay. Measuring quality and interpretability of dimensionality reduction visualizations. In SafeML ICLR Workshop , 2019 .

Adrien Bibal, Viet Minh Vu, G´ eraldin Nanfack, and Benoit Fr´ enay. Explaining t-SNE embeddings locally by adapting LIME. In ESANN , pages 393 -398 , 2020 .

- Adrien Bibal, Antoine Clarinval, Bruno Dumas, and Benoit Fr´ enay. IXVC: An interactive pipeline for explaining visual clusters in dimensionality reduction visualizations with decision trees. Array , 11 : 100080 , 2021 a.
- Adrien Bibal, Rebecca Marion, Rainer von Sachs, and Benoit Fr´ enay. BIOT: Explaining multidimensional nonlinear MDS embeddings using the Best Interpretable Orthogonal Transformation. Neurocomputing , 453 : 109 -118 , 2021 b.
- Christopher Bishop. Bayesian PCA. In Advances in Neural Information Processing Systems , volume 11 , 1998 .
- Christopher Bishop, Geoffrey E. Hinton, and Iain G. D. Strachan. GTM through time. In International Conference on Artificial Neural Networks , pages 111 -116 , 1997 a.
- Christopher M Bishop and Michael E Tipping. A hierarchical latent variable model for data visualization. IEEE Transactions on Pattern Analysis and Machine Intelligence , 20 ( 3 ): 281 -293 , 1998 .
- Christopher M Bishop, Markus Svens´ en, and Christopher KI Williams. Magnification factors for the GTM algorithm. In International Conference on Artificial Neural Networks , pages 64 -69 , 1997 b.
- Christopher M Bishop, Markus Svens´ en, and Christopher KI Williams. GTM: The generative topographic mapping. Neural Computation , 10 ( 1 ): 215 -234 , 1998 .
- Jan Niklas B¨ ohm, Philipp Berens, and Dmitry Kobak. Attraction-repulsion spectrum in neighbor embeddings. Journal of Machine Learning Research , 23 ( 95 ): 1 -32 , 2022 .
- Jan Niklas B¨ ohm, Philipp Berens, and Dmitry Kobak. Unsupervised visualization of image datasets using contrastive learning. In International Conference on Learning Representations , pages 1 -21 , 2023 .
- Jan Niklas B¨ ohm, Marius Keute, Alica Guzm´ an, Sebastian Damrich, Andrew Draganov, and Dmitry Kobak. Node Embeddings via Neighbor Embeddings. arXiv , 2025 .
- Ingwer Borg and Patrick J F Groenen. Modern multidimensional scaling: theory and applications . Springer Science & Business Media, 1997 .
- Gerard A Bouland, Ahmed Mahfouz, and Marcel JT Reinders. Consequences and opportunities arising due to sparser single-cell RNA-seq datasets. Genome Biology , 24 ( 1 ): 86 , 2023 .
- George EP Box. Robustness in the strategy of scientific model building. In Robustness in Statistics , pages 201 -236 . Elsevier, 1979 .
- Kerstin Bunte, Michael Biehl, and Barbara Hammer. A general framework for dimensionality reducing data visualization mapping. Neural Computation , 24 ( 3 ): 771 -804 , 2012 a.
- Kerstin Bunte, Petra Schneider, Barbara Hammer, FrankMichael Schleif, Thomas Villmann, and Michael Biehl. Limited rank matrix learning, discriminative dimension reduction and visualization. Neural Networks , 26 : 159 -173 , 2012 b.
- Tony Cai and Rong Ma. Theoretical foundations of t-SNE for visualizing high-dimensional clustered data. Journal of Machine Learning Research , 23 ( 301 ): 1 -54 , 2022 .
- Francesco Camastra and Antonino Staiano. Intrinsic dimension estimation: Advances and open problems. Information Sciences , 328 : 26 -41 , 2016 .
- Emmanuel J Cand` es, Xiaodong Li, Yi Ma, and John Wright. Robust principal component analysis? Journal of the ACM (JACM) , 58 ( 3 ): 1 -37 , 2011 .
- Miguel Carreira-Perpin´ an. The Elastic Embedding Algorithm for Dimensionality Reduction. In International Conference on Machine Learning , volume 10 , pages 167 -174 , 2010 .
- Miguel A Carreira-Perpin´ an and Max Vladymyrov. A fast, universal algorithm to learn parametric nonlinear embeddings. In Advances in Neural Information Processing Systems , volume 28 , 2015 .
- David M Chan, Roshan Rao, Forrest Huang, and John F Canny. t-SNE-CUDA: GPU-Accelerated t-SNE and its Applications to Modern Data. In International Symposium on Computer Architecture and High Performance Computing , pages 330 -338 , 2018 .
- Tara Chari and Lior Pachter. The specious art of single-cell genomics. PLOS Computational Biology , 19 ( 8 ):e 1011288 , 2023 .
- Yichen Cheng, Xinlei Wang, and Yusen Xia. Supervised t-distributed stochastic neighbor embedding for data visualization and classification. INFORMS Journal on Computing , 33 ( 2 ): 566 -585 , 2021 .
- Leena Chennuru Vankadara and Ulrike von Luxburg. Measures of distortion for machine learning. In Advances in Neural Information Processing Systems , volume 31 , 2018 .
- Ronald R Coifman and St´ ephane Lafon. Diffusion Maps. Applied and Computational Harmonic Analysis , 21 ( 1 ): 5 -30 , 2006 .

- Pierre Comon. Independent component analysis, A new concept? Signal Processing , 36 ( 3 ): 287 -314 , 1994 .
- Edouard Couplet, Pierre Lambert, Michel Verleysen, Dounia Mulders, John Aldo Lee, and Cyril de Bodt. Natively Interpretable t-SNE. In AIMLAI workshop colocated with ECML-PKDD , 2023 .
- Sebastian Damrich and Fred A Hamprecht. On UMAP's true loss function. In Advances in Neural Information Processing Systems , volume 34 , pages 5798 -5809 , 2021 .
- Sebastian Damrich, Jan Niklas B¨ ohm, Fred A Hamprecht, and Dmitry Kobak. From t -SNE to UMAP with contrastive learning. In International Conference on Learning Representations , pages 1 -44 , 2023 .
- Sebastian Damrich, Philipp Berens, and Dmitry Kobak. Persistent homology for high-dimensional data based on spectral methods. In Advances in Neural Information Processing Systems , volume 38 , 2024 a.
- Sebastian Damrich, Manuel V Klockow, Philipp Berens, Fred A Hamprecht, and Dmitry Kobak. Visualizing single-cell data with the neighbor embedding spectrum. bioRxiv , pages 2024 -04 , 2024 b.
- Lorraine Daston and Peter L Galison. Objectivity . Princeton University Press, 2007 .
- Cyril de Bodt, Dounia Mulders, Michel Verleysen, and John Aldo Lee. Nonlinear Dimensionality Reduction with Missing Data using Parametric Multiple Imputations. IEEE Transactions on Neural Networks and Learning Systems , 30 ( 4 ): 1166 -1179 , 2019 .
- Cyril de Bodt, Dounia Mulders, Michel Verleysen, and John Aldo Lee. Fast multiscale neighbor embedding. IEEE Transactions on Neural Networks and Learning Systems , 33 ( 4 ): 1546 -1560 , 2022 .
- Jan de Leeuw and Patrick Mair. Shepard Diagram. In Wiley StatsRef: Statistics Reference Online . John Wiley & Sons, Ltd Chichester, UK, 2015 .
- Pierre Demartines and Jeanny H´ erault. Curvilinear component analysis: a self-organizing neural network for nonlinear mapping of data sets. IEEE Transactions on Neural Networks , 8 ( 1 ): 148 -154 , 1997 .
- Persi Diaconis, Sharad Goel, and Susan Holmes. Horseshoes in Multidimensional Scaling And Local Kernel Methods. The Annals of Applied Statistics , 2 ( 3 ): 777 -807 , 2008 .
- Alex Diaz-Papkovich, Luke Anderson-Trocm´ e, Chief BenEghan, and Simon Gravel. UMAP reveals cryptic population structure and phenotype heterogeneity in large genomic cohorts. PLoS Genetics , 15 ( 11 ):e 1008432 , 2019 .
- Alex Diaz-Papkovich, Luke Anderson-Trocm´ e, and Simon Gravel. A review of UMAP in population genetics. Journal of Human Genetics , 66 ( 1 ): 85 -91 , 2021 .
- Alex Diaz-Papkovich, Shadi Zabad, Chief Ben-Eghan, Luke Anderson-Trocm´ e, Georgette Femerling, Vikram Nathan, Jenisha Patel, and Simon Gravel. Topological stratification of continuous genetic variation in large biobanks. bioRxiv , 2023 .
- Seoyoung Doh, Hyeon Jeon, Sungbok Shin, Ghulam Jilani Quadri, Nam Wook Kim, and Jinwook Seo. Understanding bias in perceiving dimensionality reduction projections. arXiv preprint arXiv: 2507 . 20805 , 2025 .
- David L Donoho and Carrie Grimes. Hessian eigenmaps: Locally linear embedding techniques for highdimensional data. Proceedings of the National Academy of Sciences , 100 ( 10 ): 5591 -5596 , 2003 .
- Andres F. Duque, Sacha Morin, Guy Wolf, and Kevin R. Moon. Geometry Regularized Autoencoders. IEEE Transactions on Pattern Analysis and Machine Intelligence , 45 ( 6 ): 7381 -7394 , 2023 .
- Andr´ es F. Duque, Sacha Morin, Guy Wolf, and Kevin Moon. Extendable and invertible manifold learning with geometry regularized autoencoders. In IEEE International Conference on Big Data (Big Data) , pages 5027 -5036 , 2020 .
- Janani Durairaj, Andrew M Waterhouse, Toomas Mets, Tetiana Brodiazhenko, Minhal Abdullah, Gabriel Studer, Gerardo Tauriello, Mehmet Akdel, Antonina Andreeva, Alex Bateman, et al. Uncovering new families and folds in the natural protein universe. Nature , 622 ( 7983 ): 646 -653 , 2023 .
- Klaus Eckelt, Andreas Hinterreiter, Patrick Adelberger, Conny Walchshofer, Vaishali Dhanoa, Christina Humer, Moritz Heckmann, Christian Steinparz, and Marc Streit. Visual Exploration of Relationships and Structure in Low-Dimensional Embeddings. IEEE Transactions on Visualization and Computer Graphics , 29 ( 7 ): 3312 -3326 , 2022 .
- Edelsbrunner, Letscher, and Zomorodian. Topological persistence and simplification. Discrete & Computational Geometry , 28 ( 4 ): 511 -533 , 2002 .
- Mateus Espadoto, Rafael M Martins, Andreas Kerren, Nina ST Hirata, and Alexandru C Telea. Toward a quantitative survey of dimension reduction techniques. IEEE Transactions on Visualization and Computer Graphics , 27 ( 3 ): 2153 -2173 , 2019 .
- BS Everett. An Introduction to Latent Variable Models . Springer Netherlands, 1984 .

- Stephen France and Douglas Carroll. Development of an agreement metric based upon the RAND index for the evaluation of dimensionality reduction techniques, with applications to mapping customer data. In International Workshop on Machine Learning and Data Mining in Pattern Recognition , pages 499 -517 , 2007 .
- Damien Francois, Vincent Wertz, and Michel Verleysen. The concentration of fractional distances. IEEE Trans. Knowl. Data Eng. , 19 ( 7 ): 873 -886 , 2007 .
- Karl Ruben Gabriel. The biplot graphic display of matrices with application to principal component analysis. Biometrika , 58 ( 3 ): 453 -467 , 1971 .
- Abraham Garc´ ıa-Aliaga, Mois´ es Marquina, Javier Coter´ on, Asier Rodr´ ıguez-Gonz´ alez, and Sergio Luengo-S´ anchez. In-game behaviour analysis of football players using machine learning techniques based on player statistics. International Journal of Sports Science & Coaching , 16 ( 1 ): 148 -157 , 2021 .
- Xin Geng, De-Chuan Zhan, and Zhi-Hua Zhou. Supervised nonlinear dimensionality reduction for visualization and classification. IEEE Transactions on Systems, Man, and Cybernetics, Part B (Cybernetics) , 35 ( 6 ): 1098 -1107 , 2005 .
- Benyamin Ghojogh, Mark Crowley, Fakhri Karray, and Ali Ghodsi. Elements of dimensionality reduction and manifold learning . Springer, 2023 .
- Scott Gigante, Adam S Charles, Smita Krishnaswamy, and Gal Mishne. Visualizing the PHATE of Neural Networks. In Advances in Neural Information Processing Systems , volume 32 , 2019 .
- Anna C Gilbert and Rishi Sonthalia. Unsupervised metric learning in presence of missing data. In 56 th Annual Allerton Conference on Communication, Control, and Computing (Allerton) , pages 313 -321 , 2018 .
- Thomas Gilovich. How we know what isn't so: The fallibility of human reason in everyday life . The Free Press, 1991 .
- Andrej Gisbrecht, Alexander Schulz, and Barbara Hammer. Parametric nonlinear dimensionality reduction using kernel t-SNE. Neurocomputing , 147 : 71 -82 , 2015 .
- Jacob Goldberger, Geoffrey E Hinton, Sam Roweis, and Russ R Salakhutdinov. Neighbourhood components analysis. In Advances in Neural Information Processing Systems , volume 17 , 2004 .
- Rita Gonz´ alez-M´ arquez, Luca Schmidt, Benjamin M Schmidt, Philipp Berens, and Dmitry Kobak. The landscape of biomedical research. Patterns , 5 ( 6 ), 2024 .
- John C Gower. Some distance properties of latent root and vector methods used in multivariate analysis. Biometrika , 53 ( 3 -4 ): 325 -338 , 1966 .
- MJ Greenacre. Theory and applications of correspondence analysis . Academic Press, 1984 .
- Andreea Griparis, Daniela Faur, and Mihai Datcu. A dimensionality reduction approach to support visual data mining: Co-ranking-based evaluation. In International Conference on Communications , pages 391 -394 , 2016 .
- Maarten Grootendorst. BERTopic: Neural topic modeling with a class-based TF-IDF procedure. arXiv , 2022 .
- Laleh Haghverdi, Florian Buettner, and Fabian J Theis. Diffusion maps for high-dimensional single-cell analysis of differentiation data. Bioinformatics , 31 ( 18 ): 2989 -2998 , 2015 .
- Laureta Hajderanj, Isakh Weheliye, and Daqing Chen. A new supervised t-SNE with dissimilarity measure for effective data visualization and classification. In International Conference on Software and Information Engineering , pages 232 -236 , 2019 .
- John Healy and Leland McInnes. Uniform manifold approximation and projection. Nature Reviews Methods Primers , 4 ( 1 ): 82 , 2024 .
- Jeffrey Heer and George Robertson. Animated Transitions in Statistical Data Graphics. IEEE Transactions on Visualization and Computer Graphics , 13 ( 6 ): 1240 -1247 , 2007 .
- Christian Hennig. What are the true clusters? Pattern Recognition Letters , 64 : 53 -62 , 2015 .
- Heulot, M. Aupetit, and J-D. Fekete. ProxiLens: Interactive Exploration of High-Dimensional Data using Projections. In EuroVis Workshop on Visual Analytics using Multidimensional Projections , 2013 .
- Geoffrey Hinton and Sam Roweis. Stochastic neighbor embedding. In Advances in Neural Information Processing Systems , volume 15 , pages 833 -840 , 2002 .
- Geoffrey E Hinton and Ruslan R Salakhutdinov. Reducing the dimensionality of data with neural networks. Science , 313 ( 5786 ): 504 -507 , 2006 .
- Rebecca D Hodge, Trygve E Bakken, Jeremy A Miller, Kimberly A Smith, Eliza R Barkan, Lucas T Graybuck, Jennie L Close, Brian Long, Nelson Johansen, Osnat Penn, et al. Conserved cell types with divergent features in human versus mouse cortex. Nature , 573 ( 7772 ): 61 -68 , 2019 .

- Thomas H¨ ollt, Anna Vilanova, Nicola Pezzotti, Boudewijn PF Lelieveldt, and Helwig Hauser. Focus+ context exploration of hierarchical embeddings. 38 ( 3 ): 569 -579 , 2019 .
- Harold Hotelling. Analysis of a complex of statistical variables into principal components. Journal of Educational Psychology , 24 ( 6 ): 417 -441 , 1933 .
- Harold Hotelling. Relations Between Two Sets of Variates. Biometrika , 28 ( 3 / 4 ): 321 -377 , 1936 .
- Haiyang Huang, Yingfan Wang, Cynthia Rudin, and Edward P Browne. Towards a comprehensive evaluation of dimension reduction methods for transcriptomic data visualization. Communications Biology , 5 ( 1 ), 2022 .
- Haiyang Huang, Yingfan Wang, and Cynthia Rudin. Navigating the Effect of Parametrization for Dimensionality Reduction. In Conference on Neural Information Processing Systems , 2024 .
- Guillaume Huguet, Alexander Tong, Bastian Rieck, Jessie Huang, Manik Kuchroo, Matthew Hirn, Guy Wolf, and Smita Krishnaswamy. Time-Inhomogeneous Diffusion Geometry and Topology. SIAM Journal on Mathematics of Data Science , 5 ( 2 ): 346 -372 , 2023 .
- Guillaume Huguet, Alexander Tong, Edward De Brouwer, Yanlei Zhang, Guy Wolf, Ian Adelstein, and Smita Krishnaswamy. A Heat Diffusion Perspective on Geodesic Preserving Dimensionality Reduction. In Advances in Neural Information Processing Systems , volume 36 , 2024 .
- Sjoerd MH Huisman, Baldur Van Lew, Ahmed Mahfouz, Nicola Pezzotti, Thomas H¨ ollt, Lieke Michielsen, Anna Vilanova, Marcel JT Reinders, and Boudewijn PF Lelieveldt. Brainscope: interactive visual exploration of the spatial and temporal human brain transcriptome. Nucleic Acids Research , 45 ( 10 ):e 83 -e 83 , 2017 .
- Alan Julian Izenman. Reduced-rank regression for the multivariate linear model. Journal of Multivariate Analysis , 5 ( 2 ): 248 -264 , 1975 .
- Mathieu Jacomy, Tommaso Venturini, Sebastien Heymann, and Mathieu Bastian. ForceAtlas 2 , a continuous graph layout algorithm for handy network visualization designed for the Gephi software. PloS one , 9 ( 6 ): e 98679 , 2014 .
- Cheongjae Jang, Yung-Kyun Noh, and Frank Chongwoo Park. A Riemannian geometric framework for manifold learning of non-Euclidean data. Advances in Data Analysis and Classification , 15 ( 3 ): 673 -699 , 2021 .
- Hyeon Jeon, Jeongin Park, Sungbok Shin, and Jinwook Seo. Stop misusing t-SNE and UMAP for visual analytics. arXiv preprint arXiv: 2506 . 08725 , 2025 .
- Kui Jia, Lin Sun, Shenghua Gao, Zhan Song, and Bertram E Shi. Laplacian auto-encoders: An explicit learning of nonlinear data manifold. Neurocomputing , 160 : 250 -260 , 2015 .
- William B. Johnson and Joram Lindenstrauss. Extensions of Lipschitz mappings into Hilbert space. Contemporary Mathematics , 26 : 189 -206 , 1984 .
- Jolicoeur and J. E. Mosimann. Size and shape variation in the painted turtle. A principal component analysis. Growth , 24 : 339 -354 , 1960 .
- Pierre Jolicoeur. Multivariate geographical variation in the wolf Canis lupus L. Evolution , pages 283 -299 , 1959 .
- Ian T Jolliffe. Principal Component Analysis and Factor Analysis. In Principal Component Analysis , pages 115 -128 . Springer, 1986 .
- Eser Kandogan. Just-in-time annotation of clusters, outliers, and trends in point-based data visualizations. In IEEE Conference on Visual Analytics Science and Technology (V AST) , pages 73 -82 , 2012 .
- Sabina Kanton, Michael James Boyle, Zhisong He, Malgorzata Santel, Anne Weigert, F´ atima Sanch´ ıs-Calleja, Patricia Guijarro, Leila Sidow, Jonas Simon Fleck, Dingding Han, Zhengzong Qian, Michael Heide, Wieland B. Huttner, Philipp Khaitovich, Svante P¨ a¨ abo, Barbara Treutlein, and J. Gray Camp. Organoid singlecell genomic atlas uncovers human-specific features of brain development. Nature , 574 ( 7778 ): 418 -422 , 2019 .
- Jon Kleinberg. An impossibility theorem for clustering. In Advances in Neural Information Processing Systems , volume 15 , 2002 .
- Dmitry Kobak and Philipp Berens. The art of using t-SNE for single-cell transcriptomics. Nature Communications , 10 ( 1 ), 2019 .
- Dmitry Kobak and George C Linderman. Initialization is critical for preserving global data structure in both t-SNE and UMAP. Nature Biotechnology , 39 ( 2 ): 156 -157 , 2021 .
- Dmitry Kobak, Wieland Brendel, Christos Constantinidis, Claudia E Feierstein, Adam Kepecs, Zachary F Mainen, Xue-Lian Qi, Ranulfo Romo, Naoshige Uchida, and Christian K Machens. Demixed principal component analysis of neural population data. eLife , 5 :e 10989 , 2016 .

- Dmitry Kobak, George Linderman, Stefan Steinerberger, Yuval Kluger, and Philipp Berens. Heavy-tailed kernels reveal a finer cluster structure in t-SNE visualisations. In Joint European Conference on Machine Learning and Knowledge Discovery in Databases , pages 124 -139 , 2019 .
- Dmitry Kobak, Fred A. Hamprecht, Smita Krishnaswamy, Gal Mishne, and Sebastian Damrich. Low-Dimensional Embeddings of High-Dimensional Data: Algorithms and Applications (Dagstuhl Seminar 24122 ). Dagstuhl Reports , 14 ( 3 ): 92 -115 , 2024 .
- Samson J. Koelle, Hanyu Zhang, Marina Meila, and YuChia Chen. Manifold Coordinates with Physical Meaning. Journal of Machine Learning Research , 23 ( 133 ): 1 -57 , 2022 .
- Samson J Koelle, Hanyu Zhang, Octavian-Vlad Murad, and Marina Meila. Consistency of dictionary-based manifold learning. In International Conference on Artificial Intelligence and Statistics , pages 4348 -4356 , 2024 .
- Koffka. Principles of Gestalt psychology. Harcourt, Brace, 1935 .
- Dhruv Kohli, Alexander Cloninger, and Gal Mishne. LDLE: Low distortion local eigenmaps. Journal of Machine Learning Research , 22 ( 282 ): 1 -64 , 2021 .
- Dhruv Kohli, Johannes S Nieuwenhuis, Alexander Cloninger, Gal Mishne, and Devika Narain. RATS: Unsupervised manifold learning using low-distortion alignment of tangent spaces. bioRxiv , pages 2024 -10 , 2024 .
- Alexey Kroshnin, Eugene Stepanov, and Dario Trevisan. Infinite multidimensional scaling for metric measure spaces. ESAIM: Control, Optimisation and Calculus of Variations , 28 ( 58 ), 2022 .
- Joseph B Kruskal. Multidimensional scaling by optimizing goodness of fit to a nonmetric hypothesis. Psychometrika , 29 ( 1 ): 1 -27 , 1964 a.
- Joseph B Kruskal. Nonmetric multidimensional scaling: a numerical method. Psychometrika , 29 ( 2 ): 115 -129 , 1964 b.
- Manik Kuchroo, Jessie Huang, Patrick Wong, JeanChristophe Grenier, Dennis Shung, Alexander Tong, Carolina Lucas, Jon Klein, Daniel B Burkhardt, Scott Gigante, et al. Multiscale PHATE identifies multimodal signatures of COVID19 . Nature Biotechnology , 40 ( 5 ): 681 -691 , 2022 .
- Gioele La Manno, Kimberly Siletti, Alessandro Furlan, Daniel Gyllborg, Elin Vinsland, Alejandro Mossi Albiach, Christoffer Mattsson Langseth, Irina Khven, Alex R Lederer, Lisa M Dratva, et al. Molecular architecture of
- the developing mouse brain. Nature , 596 ( 7870 ): 92 -96 , 2021 .
- Stephane Lafon, Yosi Keller, and Ronald R Coifman. Data fusion and multicue data matching by diffusion maps. IEEE Transactions on Pattern Analysis and Machine Intelligence , 28 ( 11 ): 1784 -1797 , 2006 .
- Pierre Lambert, Cyril de Bodt, Michel Verleysen, and John A Lee. SQuadMDS: A lean Stochastic Quartet MDS improving global structure preservation in neighbor embedding like t-SNE and UMAP. Neurocomputing , 503 : 17 -27 , 2022 a.
- Pierre Lambert, Rebecca Marion, Julien Albert, Emmanuel Jean, Sacha Corbugy, and Cyril de Bodt. Globally local and fast explanations of t-SNE-like nonlinear embeddings. In AIMLAI workshop co-located with ACM International Conference on Information and Knowledge Management , 2022 b.
- Kasper Green Larsen and Jelani Nelson. Optimality of the Johnson-Lindenstrauss lemma. In IEEE 58 th Annual Symposium on Foundations of Computer Science (FOCS) , pages 633 -638 , 2017 .
- Jan Lause, Philipp Berens, and Dmitry Kobak. Analytic Pearson residuals for normalization of single-cell RNAseq UMI data. Genome Biology , 22 : 1 -20 , 2021 .
- Jan Lause, Dmitry Kobak, and Philipp Berens. The art of seeing the elephant in the room: 2 D embeddings of single-cell data do make sense. bioRxiv , pages 2024 -03 , 2024 .
- Neil Lawrence. Gaussian process latent variable models for visualisation of high dimensional data. In Advances in Neural Information Processing Systems , volume 16 , 2003 .
- Mikhail A Lebedev, Alexei Ossadtchi, Nil Adell Mill, N´ uria Armengol Urp´ ı, Maria R Cervera, and Miguel AL Nicolelis. Analysis of neuronal ensemble activity reveals the pitfalls and shortcomings of rotation dynamics. Scientific Reports , 9 ( 1 ): 18978 , 2019 .
- A. Lee and M. Verleysen. Shift-invariant similarities circumvent distance concentration in stochastic neighbor embedding and variants. Procedia Computer Science , 4 : 538 -547 , 2011 .
- John A Lee and Michel Verleysen. Nonlinear dimensionality reduction . Springer Science & Business Media, 2007 .
- John A Lee and Michel Verleysen. Quality assessment of dimensionality reduction: Rank-based criteria. Neurocomputing , 72 ( 7 ): 1431 -1443 , 2009 .

- John A Lee, Diego H Peluffo-Ord´ o˜ nez, and Michel Verleysen. Multi-scale similarities in stochastic neighbour embedding: Reducing dimensionality while preserving both local and global structure. Neurocomputing , 169 : 246 -261 , 2015 .
- John A. Lee, Edouard Couplet, Pierre Lambert, Ludovic Journaux, Dounia Mulders, Cyril de Bodt, and Michel Verleysen. Forget early exaggeration in t-SNE: early hierarchization preserves global structure. In ESANN , pages 321 -326 , 2024 .
- Sylvain Lespinats and Micha¨ el Aupetit. CheckViz: Sanity Check and Topological Clues for Linear and NonLinear Mappings. Computer Graphics Forum , 30 ( 1 ): 113 -125 , 2011 .
- Sylvain Lespinats, Benoit Colange, and Denys Dutykh. Nonlinear Dimensionality Reduction Techniques . Springer, 2022 .
- Elizaveta Levina and Peter Bickel. Maximum likelihood estimation of intrinsic dimension. In Advances in Neural Information Processing Systems , volume 17 , 2004 .
- Lewis, L. Van der Maaten, and V. de Sa. A Behavioral Investigation of Dimensionality Reduction. In Annual Meeting of the Cognitive Science Society , volume 34 , 2012 .
- Chang Li, Julian Thijssen, Thomas Kroes, Mitchell de Boer, Tamim Abdelaal, Thomas H¨ ollt, and Boudewijn Lelieveldt. Spacewalker enables interactive gradient exploration for spatial transcriptomics data. Cell Reports Methods , 3 ( 12 ), 2023 .
- Chun-Guang Li and Jun Guo. Supervised isomap with explicit mapping. In International Conference on Innovative Computing, Information and Control , volume 3 , pages 345 -348 , 2006 .
- Henry Li, Ofir Lindenbaum, Xiuyuan Cheng, and Alexander Cloninger. Variational diffusion autoencoders with random walk sampling. In European Conference on Computer Vision , pages 362 -378 , 2020 .
- Na Li, Vincent van Unen, Thomas H¨ ollt, Allan Thompson, Jeroen van Bergen, Nicola Pezzotti, Elmar Eisemann, Anna Vilanova, Susana M Chuva de Sousa Lopes, Boudewijn PF Lelieveldt, et al. Mass cytometry reveals innate lymphoid cell differentiation pathways in the human fetal intestine. Journal of Experimental Medicine , 215 ( 5 ): 1383 -1396 , 2018 .
- Siyuan Li, Haitao Lin, Zelin Zang, Lirong Wu, Jun Xia, and Stan Z Li. Invertible manifold learning for dimension reduction. In ECML PKDD , pages 713 -728 , 2021 .
- Sunhyuk Lim and Facundo M´ emoli. Classical multidimensional scaling on metric measure spaces. Information and Inference: A Journal of the IMA , 13 ( 2 ):iaae 007 , 2024 .
- Ya-Wei Eileen Lin, Ronald R. Coifman, Gal Mishne, and Ronen Talmon. Hyperbolic Diffusion Embedding and Distance for Hierarchical Representation Learning. In International Conference on Machine Learning , volume 202 , pages 21003 -21025 , 2023 .
- George C Linderman and Stefan Steinerberger. Dimensionality reduction via dynamical systems: the case of t-SNE. SIAM Review , 64 ( 1 ): 153 -178 , 2022 .
- George C Linderman, Manas Rachh, Jeremy G Hoskins, Stefan Steinerberger, and Yuval Kluger. Fast interpolation-based t-SNE for improved visualization of single-cell RNA-seq data. Nature Methods , 16 ( 3 ): 243 -245 , 2019 .
- Yang Liu and Jeffrey Heer. Somewhere Over the Rainbow: An Empirical Assessment of Quantitative Colormaps. In Conference on Human Factors in Computing Systems , pages 1 -12 , 2018 .
- Andrew W Long and Andrew L Ferguson. Landmark diffusion maps (L-dMaps): Accelerated manifold learning out-of-sample extension. Applied and Computational Harmonic Analysis , 47 ( 1 ): 190 -211 , 2019 .
- Andreas Loukas. Graph reduction with spectral and cut guarantees. Journal of Machine Learning Research , 20 ( 116 ): 1 -42 , 2019 .
- Catherine Lozupone and Rob Knight. UniFrac: a new phylogenetic method for comparing microbial communities. Applied and Environmental Microbiology , 71 ( 12 ): 8228 -8235 , 2005 .
- Alister Machado, Michael Behrisch, and Alexandru Telea. Necessary but not Sufficient: Limitations of Projection Quality Metrics. In Computer Graphics Forum , page e 70101 , 2025 .
- Scott Makeig, Anthony Bell, Tzyy-Ping Jung, and Terrence J Sejnowski. Independent Component Analysis of Electroencephalographic Data. In Advances in Neural Information Processing Systems , volume 8 , 1995 .
- Wilson E Marc´ ılio-Jr, Danilo M Eler, Fernando V Paulovich, and Rafael M Martins. HUMAP: hierarchical uniform manifold approximation and projection. IEEE Transactions on Visualization and Computer Graphics , 2024 .

- Rafael Messias Martins, Danilo Barbosa Coimbra, Rosane Minghim, and A.C. Telea. Visual analysis of dimensionality reduction quality for parameterized projections. Computers & Graphics , 41 : 26 -42 , 2014 .
- Leland McInnes. Glasbey Categorical Color Palette Tools. https://pypi.org/project/glasbey/ , Jun 2024 .
- Leland McInnes, John Healy, and James Melville. Umap: Uniform manifold approximation and projection for dimension reduction. arXiv preprint arXiv: 1802 . 03426 , 2018 .
- Marina Meil˘ a and Hanyu Zhang. Manifold learning: What, how, and why. Annual Review of Statistics and Its Application , 11 , 2024 .
- Gal Mishne, Ronen Talmon, Ron Meir, Jackie Schiller, Maria Lavzin, Uri Dubin, and Ronald R Coifman. Hierarchical coupled-geometry analysis for neuronal structure and activity pattern discovery. IEEE Journal of Selected Topics in Signal Processing , 10 ( 7 ): 1238 -1253 , 2016 .
- Gal Mishne, Eric Chi, and Ronald Coifman. Co-manifold learning with missing data. In International Conference on Machine Learning , pages 4605 -4614 , 2019 a.
- Gal Mishne, Uri Shaham, Alexander Cloninger, and Israel Cohen. Diffusion nets. Applied and Computational Harmonic Analysis , 47 ( 2 ): 259 -285 , 2019 b.
- Bassam Mokbel, Andrej Gisbrecht, and Barbara Hammer. On the effect of clustering on quality assessment measures for dimensionality reduction. In NIPS workshop on Challenges of Data Visualization , 2010 .
- Bassam Mokbel, Andrej Gisbrecht, and Barbara Hammer. Quality Assessment Measures for Dimensionality Reduction Applied on Clustering. In ICOLE , page 75 , 2011 .
- Kevin R Moon, David Van Dijk, Zheng Wang, Scott Gigante, Daniel B Burkhardt, William S Chen, Kristina Yim, Antonia van den Elzen, Matthew J Hirn, Ronald R Coifman, et al. Visualizing structure and transitions in high-dimensional biological data. Nature Biotechnology , 37 ( 12 ): 1482 -1492 , 2019 .
- Michael Moor, Max Horn, Bastian Rieck, and Karsten Borgwardt. Topological Autoencoders. In International Conference on Machine Learning , volume 119 , pages 7045 -7054 , 2020 .
- Morariu, A. Bibal, R. Cutura, B. Frenay, and M. Sedlmair. Predicting User Preferences of Dimensionality Reduction Embedding Quality. IEEE Transactions on Visualization & Computer Graphics , 29 ( 01 ): 745 -755 , 2023 .
- James T Morton, Liam Toran, Anna Edlund, Jessica L Metcalf, Christian Lauber, and Rob Knight. Uncovering the horseshoe effect in microbial analyses. Msystems , 2 ( 1 ): 10 -1128 , 2017 .
- Tamara Munzner. Visualization Analysis and Design . CRC Press, 2014 .
- Ian T Nabney, Yi Sun, Peter Tino, and Ata Kab´ an. Semisupervised learning of hierarchical latent trait models for data visualization. IEEE Transactions on Knowledge and Data Engineering , 17 ( 3 ): 384 -400 , 2005 .
- Boaz Nadler, Stephane Lafon, Ioannis Kevrekidis, and Ronald R Coifman. Diffusion maps, spectral clustering and eigenfunctions of Fokker-Planck operators. In Advances in Neural Information Processing Systems , pages 955 -962 , 2006 .
- Philipp Nazari, Sebastian Damrich, and Fred A Hamprecht. Geometric autoencoders: what you see is what you decode. In International Conference on Machine Learning , pages 25834 -25857 , 2023 .
- Erich Neuwirth. RColorBrewer: ColorBrewer Palettes, 2022 . URL https://cran.r-project.org/web/ packages/RColorBrewer/index.html .
- Andrew Ng, Michael Jordan, and Yair Weiss. On Spectral Clustering: Analysis and an algorithm. In Advances in Neural Information Processing Systems , volume 14 , 2001 .
- Lan Huong Nguyen and Susan Holmes. Ten quick tips for effective dimensionality reduction. PLoS Computational Biology , 15 ( 6 ):e 1006907 , 2019 .
- Andreas Noack. Modularity clustering is force-directed layout. Physical Review E , 79 ( 2 ): 026102 , 2009 .
- Maximilian Noichl. Modeling the structure of recent philosophy. Synthese , 198 ( 6 ): 5089 -5100 , 2021 .
- Maximilian Noichl. How localized are computational templates? A machine learning approach. Synthese , 201 ( 3 ), 2023 .
- Corey J Nolet, Victor Lafargue, Edward Raff, Thejaswi Nanditale, Tim Oates, John Zedlewski, and Joshua Patterson. Bringing UMAP closer to the speed of light with GPU acceleration. In AAAI Conference on Artificial Intelligence , volume 35 , pages 418 -426 , 2021 .
- Nomic AI. DeepScatter, 2025 . URL https://github.com/ nomic-ai/deepscatter .
- Luis Gustavo Nonato and Michael Aupetit. Multidimensional projection for visual analytics: Linking techniques with distortions, tasks, and layout enrichment. IEEE Transactions on Visualization and Computer Graphics , 25 ( 8 ): 2650 -2673 , 2018 .

- David Novak, Cyril de Bodt, Pierre Lambert, John A Lee, Sofie Van Gassen, and Yvan Saeys. A framework for quantifiable local and global structure preservation in single-cell dimensionality reduction. bioRxiv , 2023 .
- Olga Ovcharenko, Rita Sevastjanova, and Valentina Boeva. Feature Clock: High-Dimensional Effects in TwoDimensional Plots. In IEEE Visualization and Visual Analytics (VIS) , pages 151 -155 , 2024 .
- Katherine O'Toole and Em˝ oke- ´ Agnes Horv´ at. Novelty and cultural evolution in modern popular music. EPJ Data Science , 12 ( 1 ): 3 , 2023 .
- Lucas Pagliosa, Paulo Pagliosa, and Luis Gustavo Nonato. Understanding attribute variability in multidimensional projections. In SIBGRAPI Conference on Graphics, Patterns and Images , pages 297 -304 , 2016 .
- Gautam Pai, Ronen Talmon, Alex Bronstein, and Ron Kimmel. Dimal: Deep isometric manifold learning using sparse geodesic sampling. In IEEE Winter Conference on Applications of Computer Vision , pages 819 -828 , 2019 .
- Rahul Paul and Stephan K Chalup. A study on validating non-linear dimensionality reduction using persistent homology. Pattern Recognition Letters , 100 : 160 -166 , 2017 .
- Karl Pearson. On lines and planes of closest fit to systems of points in space. The London, Edinburgh, and Dublin Philosophical Magazine and Journal of Science , 2 ( 11 ): 559 -572 , 1901 .
- Fabian Pedregosa, Ga¨ el Varoquaux, Alexandre Gramfort, Vincent Michel, Bertrand Thirion, Olivier Grisel, Mathieu Blondel, Peter Prettenhofer, Ron Weiss, Vincent Dubourg, et al. Scikit-learn: Machine learning in Python. Journal of Machine Learning Research , 12 : 2825 -2830 , 2011 .
- Erez Peterfreund, Ofir Lindenbaum, Felix Dietrich, Tom Bertalan, Matan Gavish, Ioannis G Kevrekidis, and Ronald R Coifman. Local conformal autoencoder for standardized data coordinates. Proceedings of the National Academy of Sciences , 117 ( 49 ): 30918 -30927 , 2020 .
- Pezzotti, T. H¨ ollt, B. Lelieveldt, E. Eisemann, and A. Vilanova. Hierarchical Stochastic Neighbor Embedding. Computer Graphics Forum , 35 ( 3 ): 21 -30 , 2016 a.
- Nicola Pezzotti, Boudewijn PF Lelieveldt, Laurens Van Der Maaten, Thomas H¨ ollt, Elmar Eisemann, and Anna Vilanova. Approximated and user steerable t-SNE for progressive visual analytics. IEEE Transactions on Visualization and Computer Graphics , 23 ( 7 ): 1739 -1752 , 2016 b.
- Nicola Pezzotti, Julian Thijssen, Alexander Mordvintsev, Thomas H¨ ollt, Baldur Van Lew, Boudewijn PF Lelieveldt, Elmar Eisemann, and Anna Vilanova. GPGPU linear complexity t-SNE optimization. IEEE Transactions on Visualization and Computer Graphics , 26 ( 1 ): 1172 -1181 , 2019 .
- Pavlin G Poliˇ car, Martin Straˇ zar, and Blaˇ z Zupan. Embedding to reference t-SNE space addresses batch effects in single-cell classification. Machine Learning , 112 ( 2 ): 721 -740 , 2023 .
- Pavlin G Poliˇ car, Martin Straˇ zar, and Blaˇ z Zupan. openTSNE: a modular Python library for t-SNE dimensionality reduction and embedding. Journal of Statistical Software , 109 : 1 -30 , 2024 .
- Pavlin G. Poliˇ car and Blaˇ z Zupan. VERA: Generating Visual Explanations of Two-Dimensional Embeddings via Region Annotation. arXiv , 2024 .
- Shaun Purcell, Benjamin Neale, Kathe Todd-Brown, Lori Thomas, Manuel A. R. Ferreira, David Bender, Julian Maller, Pamela Sklar, Paul I. W. de Bakker, Mark J. Daly, and Pak C. Sham. PLINK: A Tool Set for WholeGenome Association and Population-Based Linkage Analyses. The American Journal of Human Genetics , 81 ( 3 ): 559 -575 , 2007 .
- C Radhakrishna Rao. The utilization of multiple measurements in problems of biological classification. Journal of the Royal Statistical Society. Series B (Methodological) , 10 ( 2 ): 159 -203 , 1948 .
- Jake S Rhodes, Adele Cutler, Guy Wolf, and Kevin R Moon. Random forest-based diffusion information geometry for supervised visualization and data exploration. In Statistical Signal Processing Workshop (SSP) , pages 331 -335 , 2021 .
- Jake S Rhodes, Adrien Aumon, Sacha Morin, Marc Girard, Catherine Larochelle, Elsa Brunet-Ratnasingham, Am´ elie Pagliuzza, Lorie Marchitto, Wei Zhang, Adele Cutler, et al. Gaining biological insights through supervised data visualization. bioRxiv , pages 2023 -11 , 2023 .
- Bastian Rieck and Heike Leitte. Persistent homology for the evaluation of dimensionality reduction schemes. Computer Graphics Forum , 34 ( 3 ): 431 -440 , 2015 .
- Markus Ringn´ er. What is principal component analysis? Nature Biotechnology , 26 ( 3 ): 303 -304 , 2008 .
- Duccio Rocchini, Ludovico Chieffallo, Elisa Thouverai, Rossella D'Introno, Francesca Dagostin, Emma Donini, Giles Foody, Simon Garnier, Guilherme G. Mazzochini,

- Vitezslav Moudry, Bob Rudis, Petra Simova, Michele Torresani, and Jakub Nowosad. Under the mantra: 'Make use of colorblind friendly graphs'. Environmetrics , 35 ( 6 ):e 2877 , 2024 .
- Peter J Rousseeuw. Silhouettes: a graphical aid to the interpretation and validation of cluster analysis. Journal of Computational and Applied Mathematics , 20 : 53 -65 , 1987 .
- Sam Roweis and Lawrence Saul. Nonlinear dimensionality reduction by locally linear embedding. Science , 290 ( 5500 ): 2323 -2326 , 2000 .
- Dominik Sacha, Leishi Zhang, Michael Sedlmair, John A Lee, Jaakko Peltonen, Daniel Weiskopf, Stephen C North, and Daniel A Keim. Visual interaction with dimensionality reduction: A structured literature analysis. IEEE Transactions on Visualization and Computer Graphics , 23 ( 1 ): 241 -250 , 2016 .
- Dominik Sacha, Michael Sedlmair, Leishi Zhang, John A. Lee, Jaakko Peltonen, Daniel Weiskopf, Stephen C. North, and Daniel A. Keim. What you see is what you can change: Human-centered machine learning by interactive visualization. Neurocomputing , 268 : 164 -175 , 2017 .
- Tim Sainburg, Leland McInnes, and Timothy Q Gentner. Parametric UMAP embeddings for representation and semisupervised learning. Neural Computation , 33 ( 11 ): 2881 -2907 , 2021 .
- John W Sammon. A nonlinear mapping for data structure analysis. IEEE Trans. Comput. , 100 ( 5 ): 401 -409 , 1969 .
- Federico Scala, Dmitry Kobak, Matteo Bernabucci, Yves Bernaerts, Cathryn Ren´ e Cadwell, Jesus Ramon Castro, Leonard Hartmanis, Xiaolong Jiang, Sophie Laturnus, Elanine Miranda, et al. Phenotypic variation of transcriptomic cell types in mouse motor cortex. Nature , 598 ( 7879 ): 144 -150 , 2021 .
- Benjamin Schmidt. Stable random projection: Lightweight, general-purpose dimensionality reduction for digitized libraries. Journal of Cultural Analytics , 3 ( 1 ), 2018 .
- Bernhard Sch¨ olkopf, Alexander Smola, and Klaus-Robert M¨ uller. Kernel principal component analysis. In Artificial Neural Networks - ICANN , pages 583 -588 , 1997 .
- Tobias Schreck, Tatiana von Landesberger, and Sebastian Bremm. Techniques for Precision-Based Visual Analysis of Projected Data. Information Visualization , 9 ( 3 ): 181 -193 , 2010 .
- Christin Seifert, Vedran Sabol, and Wolfgang Kienreich. Stress Maps: Analysing Local Phenomena in Dimensionality Reduction Based Visualisations. In International Symposium on Visual Analytics Science and Technology , 2010 .
- Uri Shaham, Kelly Stanton, Henry Li, Ronen Basri, Boaz Nadler, and Yuval Kluger. SpectralNet: Spectral Clustering using Deep Neural Networks. In International Conference on Learning Representations , 2018 .
- Chao Shen and Hau-Tieng Wu. Scalability and robustness of spectral embedding: landmark diffusion is all you need. Information and Inference: A Journal of the IMA , 11 ( 4 ): 1527 -1595 , 2022 .
- Roger N Shepard. The analysis of proximities: multidimensional scaling with an unknown distance function. I. Psychometrika , 27 ( 2 ): 125 -140 , 1962 a.
- Roger N Shepard. The analysis of proximities: multidimensional scaling with an unknown distance function. II. Psychometrika , 27 ( 3 ): 219 -246 , 1962 b.
- Jianbo Shi and Jitendra Malik. Normalized cuts and image segmentation. IEEE Transactions on Pattern Analysis and Machine Intelligence , 22 ( 8 ): 888 -905 , 2000 .
- Vin D. Silva and Joshua B. Tenenbaum. Global versus local methods in nonlinear dimensionality reduction. In Advances in Neural Information Processing Systems , volume 15 , pages 705 --712 , 2003 .
- Amit Singer. From graph to manifold Laplacian: The convergence rate. Applied and Computational Harmonic Analysis , 21 ( 1 ): 128 -134 , 2006 .
- Amit Singer and H-T Wu. Vector diffusion maps and the connection Laplacian. Communications on Pure and Applied Mathematics , 65 ( 8 ): 1067 -1144 , 2012 .
- Amit Singer and Hau-Tieng Wu. Spectral convergence of the connection Laplacian from random samples. Information and Inference: A Journal of the IMA , 6 ( 1 ): 58 -123 , 2017 .
- Martin Skrodzki, Nicolas F. Chaves de Plaza, Thomas H¨ ollt, Elmar Eisemann, and Klaus Hildebrandt. Navigating Perplexity: A linear relationship with the data set size in t-SNE embeddings. arXiv , 2023 .
- Le Song, Arthur Gretton, Karsten Borgwardt, and Alex Smola. Colored Maximum Variance Unfolding. In Advances in Neural Information Processing Systems , volume 20 , 2007 .
- Charles Spearman. 'General Intelligence' Objectively Determined and Measured. The American Journal of Psychology , 15 ( 2 ): 201 -292 , 1904 .

- Julian Stahnke, Marian D¨ ork, Boris M¨ uller, and Andreas Thom. Probing Projections: Interaction Techniques for Interpreting Arrangements and Errors of Dimensionality Reductions. IEEE Transactions on Visualization and Computer Graphics , 22 ( 1 ): 629 -638 , 2016 .
- Jacob L. Steenwyk and Antonis Rokas. ggpubfigs: Colorblind-Friendly Color Palettes and ggplot 2 Graphic System Extensions for Publication-Quality Scientific Figures. Microbiology Resource Announcements , 10 ( 44 ), 2021 .
- Shiquan Sun, Jiaqiang Zhu, Ying Ma, and Xiang Zhou. Accuracy, robustness and scalability of dimensionality reduction methods for single-cell RNA-seq analysis. Genome Biology , 20 : 1 -21 , 2019 .
- Ronen Talmon and Ronald R Coifman. Empirical intrinsic geometry for nonlinear modeling and time series filtering. Proceedings of the National Academy of Sciences , 110 ( 31 ): 12535 -12540 , 2013 .
- Ronen Talmon, Israel Cohen, and Sharon Gannot. Singlechannel transient interference suppression with diffusion maps. IEEE Transactions on Audio, Speech, and Language Processing , 21 ( 1 ): 132 -144 , 2012 .
- Jian Tang, Jingzhou Liu, Ming Zhang, and Qiaozhu Mei. Visualizing large-scale and high-dimensional data. In International Conference on World Wide Web , pages 287 -297 , 2016 .
- Bosiljka Tasic, Zizhen Yao, Lucas T. Graybuck, Kimberly A. Smith, Thuc Nghi Nguyen, Darren Bertagnolli, Jeff Goldy, Emma Garren, Michael N. Economo, Sarada Viswanathan, Osnat Penn, Trygve Bakken, Vilas Menon, Jeremy Miller, Olivia Fong, Karla E. Hirokawa, Kanan Lathia, Christine Rimorin, Michael Tieu, Rachael Larsen, Tamara Casper, Eliza Barkan, Matthew Kroll, Sheana Parry, Nadiya V. Shapovalova, Daniel Hirschstein, Julie Pendergraft, Heather A. Sullivan, Tae Kyung Kim, Aaron Szafer, Nick Dee, Peter Groblewski, Ian Wickersham, Ali Cetin, Julie A. Harris, Boaz P. Levi, Susan M. Sunkin, Linda Madisen, Tanya L. Daigle, Loren Looger, Amy Bernard, John Phillips, Ed Lein, Michael Hawrylycz, Karel Svoboda, Allan R. Jones, Christof Koch, and Hongkui Zeng. Shared and distinct transcriptomic cell types across neocortical areas. Nature , 563 ( 7729 ): 72 -78 , 2018 .
- Kye M Taylor and Franc ¸ois G Meyer. A random walk on image patches. SIAM Journal on Imaging Sciences , 5 ( 2 ): 688 -725 , 2012 .
- Joshua B Tenenbaum, Vin De Silva, and John C Langford. A global geometric framework for nonlinear dimensionality reduction. Science , 290 ( 5500 ): 2319 -2323 , 2000 .
- The 1000 Genomes Project Consortium. A global reference for human genetic variation. Nature , 526 ( 7571 ): 68 -74 , 2015 .
- Julian Thijssen, Zonglin Tian, and Alexandru Telea. Interactive tools for explaining multidimensional projections for high-dimensional tabular data. Computers & Graphics , 122 : 103987 , 2024 .
- Louis Leon Thurstone. Multiple factor analysis. Psychological Review , 38 ( 5 ), 1931 .
- Zonglin Tian, Xiaorui Zhai, Daan van Driel, Gijs van Steenpaal, Mateus Espadoto, and Alexandru Telea. Using multiple attribute-based explanations of multidimensional projections to explore high-dimensional data. Computers & Graphics , 98 : 93 -104 , 2021 .
- Zonglin Tian, Wouter Castelein, Tamara Mchedlidze, and Alexandru C Telea. Measuring and Interpreting the Quality of 3 DProjections of High-Dimensional Data. In International Joint Conference on Computer Vision, Imaging and Computer Graphics , pages 348 -373 , 2023 .
- Peter Tino, Ian Nabney, and Yi Sun. Using directional curvatures to visualize folding patterns of the GTM projection manifolds. In Artificial Neural Networks ICANN , pages 421 -428 , 2001 a.
- Peter Tino, Ian Nabney, Yi Sun, and Bruce S Williams. A principled approach to interactive hierarchical nonlinear visualization of high-dimensional data. Frontiers in Data Mining and Bioinformatics , 2001 b.
- Michael E Tipping and Christopher M Bishop. Mixtures of probabilistic principal component analyzers. Neural Computation , 11 ( 2 ): 443 -482 , 1999 a.
- Michael E Tipping and Christopher M Bishop. Probabilistic Principal Component Analysis. Journal of the Royal Statistical Society Series B: Statistical Methodology , 61 ( 3 ): 611 -622 , 1999 b.
- Warren S Torgerson. Multidimensional scaling: I. Theory and method. Psychometrika , 17 ( 4 ): 401 -419 , 1952 .
- John W Tukey. Exploratory data analysis . Addison-Wesley, 1977 .
- John W. Tukey. We Need Both Exploratory and Confirmatory. The American Statistician , 34 ( 1 ): 23 -25 , 1980 .
- Laurens van der Maaten. Learning a parametric embedding by preserving local structure. In Artificial Intelligence and Statistics , pages 384 -391 , 2009 .
- Laurens van der Maaten. Accelerating t-SNE using treebased algorithms. Journal of Machine Learning Research , 15 ( 1 ): 3221 -3245 , 2014 .

- Laurens van der Maaten and Geoffrey Hinton. Visualizing Data using t-SNE. Journal of Machine Learning Research , 9 ( 86 ): 2579 -2605 , 2008 .
- Vincent Van Unen, Thomas H¨ ollt, Nicola Pezzotti, Na Li, Marcel JT Reinders, Elmar Eisemann, Frits Koning, Anna Vilanova, and Boudewijn PF Lelieveldt. Visual analysis of mass cytometry data by hierarchical stochastic neighbour embedding reveals rare cell types. Nature Communications , 8 ( 1 ): 1740 , 2017 .
- Jarkko Venna, Jaakko Peltonen, Kristian Nybo, Helena Aidos, and Samuel Kaski. Information Retrieval Perspective to Nonlinear Dimensionality Reduction for Data Visualization. Journal of Machine Learning Research , 11 ( 13 ): 451 -490 , 2010 .
- Alexander Vieth, Thomas Kroes, Julian Thijssen, Baldur van Lew, Jeroen Eggermont, Soumyadeep Basu, Elmar Eisemann, Anna Vilanova, Thomas H¨ ollt, and Boudewijn Lelieveldt. ManiVault: A Flexible and Extensible Visual Analytics Framework for HighDimensional Data. IEEE Transactions on Visualization and Computer Graphics , 2023 .
- Max Vladymyrov. No Pressure! Addressing the Problem of Local Minima in Manifold Learning Algorithms. In Advances in Neural Information Processing Systems , volume 32 , 2019 .
- Max Vladymyrov and Miguel Carreira-Perpinan. Lineartime training of nonlinear low-dimensional embeddings. In Artificial Intelligence and Statistics , pages 968 -977 , 2014 .
- Ulrike Von Luxburg, Robert C Williamson, and Isabelle Guyon. Clustering: Science or art? In ICML Workshop on Unsupervised and Transfer Learning , pages 65 -79 , 2012 .
- Kaiwen Wang, Yuqiu Yang, Fangjiang Wu, Bing Song, Xinlei Wang, and Tao Wang. Comparative analysis of dimension reduction methods for cytometry by timeof-flight data. Nature Communications , 14 ( 1 ), 2023 a.
- Shu Wang, Eduardo D Sontag, and Douglas A Lauffenburger. What cannot be seen correctly in 2 D visualizations of single-cell 'omics data? Cell Systems , 14 ( 9 ): 723 -731 , 2023 b.
- Yingfan Wang, Haiyang Huang, Cynthia Rudin, and Yaron Shaposhnik. Understanding how dimension reduction tools work: an empirical approach to deciphering t-SNE, UMAP, TriMAP, and PaCMAP for data visualization. Journal of Machine Learning Research , 22 ( 201 ): 1 -73 , 2021 .
- Colin Ware and Rusty Bobrow. Motion coding for pattern detection. In Symposium on Applied Perception in Graphics and Visualization , pages 107 -110 , 2006 .
- Jeremy Wayland, Corinna Coupette, and Bastian Rieck. Mapping the Multiverse of Latent Representations. In International Conference on Machine Learning (ICML) , 2024 .
- Kilian Q Weinberger and Lawrence K Saul. An Introduction to Nonlinear Dimensionality Reduction by Maximum Variance Unfolding. In American Association for Artificial Intelligence , volume 6 , pages 1683 -1686 , 2006 .
- Lloyd Welch. Lower bounds on the maximum cross correlation of signals (Corresp.). IEEE Transactions on Information Theory , 20 ( 3 ): 397 -399 , 1974 .
- Jiazhi Xia, Yuchen Zhang, Jie Song, Yang Chen, Yunhai Wang, and Shixia Liu. Revisiting dimensionality reduction techniques for visual cluster analysis: An empirical study. IEEE Transactions on Visualization and Computer Graphics , 28 ( 1 ): 529 -539 , 2021 .
- Ruizhi Xiang, Wencan Wang, Lei Yang, Shiyuan Wang, Chaohan Xu, and Xiaowen Chen. A comparison for dimensionality reduction methods of single-cell RNAseq data. Frontiers in Genetics , 12 , 2021 .
- Itai Yanai and Martin Lercher. A hypothesis is a liability. Genome Biology , 21 : 1 -5 , 2020 .
- Zhirong Yang, Irwin King, Zenglin Xu, and Erkki Oja. Heavy-tailed symmetric stochastic neighbor embedding. In Advances in Neural Information Processing Systems , pages 2169 -2177 , 2009 .
- Zhirong Yang, Jaakko Peltonen, and Samuel Kaski. Scalable Optimization of Neighbor Embedding for Visualization. In International Conference on Machine Learning , volume 2 , pages 127 -135 , 2013 .
- Byron M Yu, John P Cunningham, Gopal Santhanam, Stephen Ryu, Krishna V Shenoy, and Maneesh Sahani. Gaussian-process factor analysis for low-dimensional single-trial analysis of neural population activity. In Advances in Neural Information Processing Systems , volume 21 , 2008 .
- Meiting Yu, Siqian Zhang, Lingjun Zhao, and Gangyao Kuang. Deep supervised t-SNE for SAR target recognition. In International Conference on Frontiers of Sensors Technologies , pages 265 -269 , 2017 .
- Jinjie Zhang and Rayan Saab. Faster binary Embeddings for preserving Euclidean distances. In International Conference on Learning Representations , 2021 .

- Zhenyue Zhang and Hongyuan Zha. Principal Manifolds and Nonlinear Dimensionality Reduction via Tangent Space Alignment. SIAM Journal on Scientific Computing , 26 ( 1 ): 313 -338 , 2004 .
- Hui Zou, Trevor Hastie, and Robert Tibshirani. Sparse Principal Component Analysis. Journal of Computational and Graphical Statistics , 15 ( 2 ): 265 -286 , 2006 .

