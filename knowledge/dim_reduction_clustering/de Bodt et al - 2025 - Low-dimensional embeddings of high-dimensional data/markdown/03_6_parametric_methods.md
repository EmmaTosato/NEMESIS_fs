## 3 . 6 Parametric methods

Except for linear and probabilistic methods, most methods described above are non-parametric, i.e., they construct an embedding without learning an explicit mapping between the high-dimensional and the lowdimensional coordinates. While flexible, one limitation of these kinds of approaches is that adding out-of-sample data into existing embeddings is not straightforward (Bengio et al., 2004 ). One family of non-linear parametric methods are auto-encoders (Hinton and Salakhutdinov, 2006 ), where geometric or topological constraints on the non-linear mapping have been used to obtain more geometrically accurate parametric embeddings of the data (Jia et al., 2015 ; Li et al., 2020 , 2021 ; Peterfreund et al., 2020 ; Moor et al., 2020 ; Duque et al., 2023 ; Nazari et al., 2023 ).

Many non-parametric methods can be converted into their parametric variants using various neural network ar-

chitectures. However, the effects of such parametrization have only recently been systematically explored (Duque et al., 2023 ; Huang et al., 2024 ). Many such approaches have been proposed for spectral embeddings Mishne et al. ( 2019 b); Shaham et al. ( 2018 ); Pai et al. ( 2019 ); Duque et al. ( 2020 ) and neighbor-embedding methods (van der Maaten, 2009 ; Bunte et al., 2012 a; Gisbrecht et al., 2015 ; Sainburg et al., 2021 ; Carreira-Perpin´ an and Vladymyrov, 2015 ; Damrich et al., 2023 ).

