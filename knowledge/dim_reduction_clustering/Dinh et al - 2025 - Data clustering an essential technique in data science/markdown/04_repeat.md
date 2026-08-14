## 4 repeat

5

- for each object in the dataset do

6

7

as shown in Algorithm 7. Instead of recalculating the centroids after all points have been assigned (as in Lloyd's algorithm), MacQueen's algorithm updates centroids incrementally as each point is assigned to a cluster. This method may converge faster in some cases due to incremental updates. However, it is not always faster than Lloyd's, and it might be more sensitive to the order of data points, especially in larger datasets (Izenman, 2008; Reddy & Vinzamuri, 2013). 8 9 10 11 12

Algorithm 2: MacQueen's K-M eans (MacQueen et al., 1967)

- 1 Randomly select k data points as initial centroids
- 2 repeat
- 3 for each data point xi do
- 4 Assign xi to the nearest centroid cj

5

Update the centroid cj as mean over all data points assigned to it so far, including xi

- 6 end
- 7 until convergence

Generally, K-M eans is e ffi cient with large datasets and is computationally straightforward, with a time complexity that generally scales linearly with the number of data points (Aggarwal, 2013). However, it often converges to a local rather than a global optimum, depending on the initial centroid positions (MacQueen et al., 1967). In addition, the algorithm tends to form clusters with convex, spherical shapes, making it less suitable for complex or non-convex structures (Anderberg, 1973). Despite these limitations, K-M eans remains popular due to its simplicity and e ff ectiveness in many practical applications, such as customer segmentation, document clustering, pattern recognition, and data preprocessing, to name a few (Han et al., 2022; Wu et al., 2008).

K-M odes (Huang, 1998) is another partitioning methods of clustering technique, extending the K-M eans algorithm. Instead of using the mean to define cluster centroids, K-M odes relies on the mode -the most frequently occurring value for each feature. It uses the S imple M atching D issimilarity measure (Dinh et al., 2025) to quantify the distance between categorical objects. The algorithm begins by randomly selecting k data points as the initial centroids. It then assigns each data point to the cluster whose centroid has the minimum dissimilarity, often measured by the number of mismatched categorical attributes.

Retest the dissimilarity of the object against the current modes

- if the nearest mode for the object belongs to a di ff erent cluster then

Reallocate the object to that cluster Update the modes of both a ff ected clusters end

end until convergence

After the assignments, the centroids are updated by determining the mode for each feature within the cluster. This process of assignment and update is repeated iteratively until the centroids stabilize or a predefined stopping criterion is met. K-M odes is computationally e ffi cient and well-suited for categorical data. Still, it requires pre-specifying the number of clusters k and can be sensitive to the initial choice of centroids.

K-P rototypes (Huang, 1998) is a clustering algorithm designed for mixed-type data, combining the principles of K-M eans and K-M odes . It uses an adapted distance function that treats each data type separately, updating numeric variables with their means and categorical variables with their modes. It e ffi ciently handles mixed data in one algorithm, rather than running separate clustering processes for each data type.

F uzzy C-M eans (FCM) (Bezdek et al., 1984) is a clustering algorithm that assigns data points to multiple clusters with varying degrees of membership, rather than forcing each point into a single cluster. FCM minimizes an objective function by iteratively updating cluster centers and fuzzy membership values. This approach is particularly e ff ective for datasets with overlapping clusters, as it allows for soft boundaries between clusters.

F uzzy K-M odes (Huang & Ng, 1999) is an extension of fuzzy clustering designed for categorical data. While F uzzy CM eans operates on numerical data and relies on Euclidean distance, F uzzy K-M odes replaces this with a dissimilarity measure tailored for categorical attributes such as the S imple M atch -ing D issimilarity measure (Dinh et al., 2025). It calculates cluster modes rather than means, while still allowing fuzzy membership, making it ideal for datasets involving categorical features.

H ierarchical A gglomerative C lustering (HAC) is a bottomup clustering approach that begins with each data point as an individual cluster and iteratively merges the closest clusters until a single cluster encompassing all data points is formed. The process is typically visualized using a dendrogram, a tree-like

### Algorithm 4: H ierarchical A gglomerative C lustering

Input: D = { xi | i = 1 , 2 , . . . , n } , initially each xi is in its own cluster.

- 1 Compute M = { dij } , the ( n × n ) matrix of pairwise dissimilarities between the clusters, where dij = d ( xi , xj ).

