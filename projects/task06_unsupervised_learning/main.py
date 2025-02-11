import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans, DBSCAN
import time
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from sklearn.manifold import TSNE
from sklearn.neighbors import NearestNeighbors


def k_means(data, k, max_iterations=100, tolerance=1e-4):
    centroids = data[np.random.choice(data.shape[0], k, replace=False)]
    closest_centroids = np.zeros(data.shape[0], dtype=int)
    for iteration in range(max_iterations):
        distances = np.sqrt(((data - centroids[:, np.newaxis]) ** 2).sum(axis=2))
        closest_centroids = np.argmin(distances, axis=0)

        new_centroids = np.array([data[closest_centroids == i].mean(axis=0) for i in range(k)])

        if np.all(np.abs(new_centroids - centroids) <= tolerance):
            break

        centroids = new_centroids

    return centroids, closest_centroids


def optimal_kmeans_clusters(data, max_k=10):
    wcss = []
    for i in range(2, max_k + 1):
        kmeans = KMeans(n_clusters=i, init='k-means++', max_iter=300, n_init=10, random_state=0)
        kmeans.fit(data)
        wcss.append(kmeans.inertia_)

    k_derivatives = np.diff(wcss)
    optimal_k = np.argmin(k_derivatives) + 2
    return optimal_k if optimal_k > 1 else 2


def optimize_dbscan_eps(data, k=5):
    neighbors = NearestNeighbors(n_neighbors=k)
    neighbors_fit = neighbors.fit(data)
    distances, indices = neighbors_fit.kneighbors(data)
    eps = np.mean(distances[:, k - 1])
    return eps


file_path = 'celltocellholdout.csv'
data = pd.read_csv(file_path)
if data['Churn'].isna().all():
    data.drop(columns=['Churn'], inplace=True)

numeric_cols = data.select_dtypes(include=[np.number]).columns
numeric_imputer = SimpleImputer(strategy='mean')
data_numeric_imputed = numeric_imputer.fit_transform(data[numeric_cols])

scaler = StandardScaler()
data_numeric_scaled = scaler.fit_transform(data_numeric_imputed)

pca_2 = PCA(n_components=2)
data_pca_2 = pca_2.fit_transform(data_numeric_scaled)

# Additionally, determine the number of components to retain 95% variance
pca_95 = PCA(n_components=0.95)
data_pca_95 = pca_95.fit_transform(data_numeric_scaled)
variance_ratio_95 = pca_95.explained_variance_ratio_.sum()
num_components_95 = pca_95.n_components_

print("Data with 2 PCA components:\n", data_pca_2)
print(f"95% variance is retained by {num_components_95} components.")

# Visualization
plt.figure(figsize=(8, 6))
plt.scatter(data_pca_2[:, 0], data_pca_2[:, 1], alpha=0.5)
plt.title('PCA 2D')
plt.xlabel('Principal Component 1')
plt.ylabel('Principal Component 2')
plt.show()

optimal_k = optimal_kmeans_clusters(data_pca_95)
print("Optimal K for KMeans:", optimal_k)

start_time = time.time()
centroids, clusters_custom = k_means(data_pca_95, optimal_k)
custom_kmeans_time = time.time() - start_time
print("Custom KMeans Time:", custom_kmeans_time, "seconds")

start_time = time.time()
kmeans = KMeans(n_clusters=optimal_k)
clusters_kmeans = kmeans.fit_predict(data_pca_95)
kmeans_time = time.time() - start_time
print("KMeans Time:", kmeans_time, "seconds")

eps_value = optimize_dbscan_eps(data_pca_95)
print("Calculated EPS for DBSCAN:", eps_value)

start_time = time.time()
dbscan = DBSCAN(eps=eps_value, min_samples=5)
clusters_dbscan = dbscan.fit_predict(data_pca_95)
dbscan_time = time.time() - start_time
print("DBSCAN Clustering Time:", dbscan_time, "seconds")

silhouette_kmeans = silhouette_score(data_pca_95, clusters_kmeans)
davies_bouldin_kmeans = davies_bouldin_score(data_pca_95, clusters_kmeans)
calinski_harabasz_kmeans = calinski_harabasz_score(data_pca_95, clusters_kmeans)

silhouette_dbscan = silhouette_score(data_pca_95, clusters_dbscan)
davies_bouldin_dbscan = davies_bouldin_score(data_pca_95, clusters_dbscan)
calinski_harabasz_dbscan = calinski_harabasz_score(data_pca_95, clusters_dbscan)

silhouette_custom = silhouette_score(data_pca_95, clusters_custom)
davies_bouldin_custom = davies_bouldin_score(data_pca_95, clusters_custom)
calinski_harabasz_custom = calinski_harabasz_score(data_pca_95, clusters_custom)

print("Custom KMeans Metrics:")
print("Silhouette Score:", silhouette_custom)
print("Davies-Bouldin Score:", davies_bouldin_custom)
print("Calinski-Harabasz Index:", calinski_harabasz_custom)

print("KMeans Metrics:")
print("Silhouette Score:", silhouette_kmeans)
print("Davies-Bouldin Score:", davies_bouldin_kmeans)
print("Calinski-Harabasz Index:", calinski_harabasz_kmeans)

print("DBSCAN Propagation Metrics:")
print("Silhouette Score:", silhouette_dbscan)
print("Davies-Bouldin Score:", davies_bouldin_dbscan)
print("Calinski-Harabasz Index:", calinski_harabasz_dbscan)

tsne = TSNE(n_components=2, perplexity=30, n_iter=250)
data_tsne = tsne.fit_transform(data_pca_95)

plt.figure(figsize=(10, 8))
plt.scatter(data_tsne[:, 0], data_tsne[:, 1], c=clusters_kmeans, cmap='viridis', alpha=0.5)
plt.title('t-SNE Visualization of KMeans Clusters')
plt.show()
