import os
import pandas as pd
from sklearn.cluster import DBSCAN, MiniBatchKMeans
import numpy as np
from sklearn.metrics.pairwise import haversine_distances
from google.cloud import bigquery

def fetch_data_by_soustype(project_id, dataset_id, table_id, soustype_name):
    """
    Fetch data from BigQuery for a specific sous-type.
    """
    client = bigquery.Client(project=project_id)
    query = f"""
    SELECT *
    FROM `{project_id}.{dataset_id}.{table_id}`
    WHERE soustype = @soustype_name
    """
    job_config = bigquery.job.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("soustype_name", "STRING", soustype_name)
        ]
    )
    query_job = client.query(query, job_config=job_config)
    return query_job.result().to_dataframe()

def cluster_data_by_soustype(project_id, dataset_id, table_id, specific_soustype=None):
    """
    Cluster the entire dataset by sous-type in memory (faster than querying one by one).
    Optionally filter by a specific sous-type for testing.
    """
    client = bigquery.Client(project=project_id)

    # Fetch all rows with non-null sous-type in one query
    query = f"""SELECT * FROM `{project_id}.{dataset_id}.{table_id}` WHERE soustype IS NOT NULL"""
    print("Fetching all data from BigQuery...")
    all_data = client.query(query).result().to_dataframe()
    print("Done. Starting clustering...")

    clustered_data_list = []
    cluster_counter = 0

    # Get unique sous-types from fetched data
    soustypes = all_data['soustype'].unique()

    # Optionally filter for a specific sous-type
    if specific_soustype:
        soustypes = [specific_soustype]

    for idx, soustype_name in enumerate(soustypes, start=1):
        if not idx % 10:
            print(f"{idx} sous-type processed out of {len(soustypes)}")

        # Filter in-memory instead of querying
        soustype_data = all_data[all_data['soustype'] == soustype_name].copy()

        # Extract latitude and longitude from geo_point_2d string
        soustype_data[['latitude', 'longitude']] = soustype_data['geo_point_2d'].str.split(',', expand=True).astype(float)

        # Drop rows with missing coordinates
        valid_geo_data = soustype_data.dropna(subset=['latitude', 'longitude'])

        # Convert coordinates to radians for Haversine distance
        earth_radius = 6371000  # in meters
        valid_geo_data['lat_rad'] = np.radians(valid_geo_data['latitude'])
        valid_geo_data['lon_rad'] = np.radians(valid_geo_data['longitude'])

        # Run DBSCAN clustering on geographic coordinates
        coords = valid_geo_data[['lat_rad', 'lon_rad']]

        """
        if len(coords) > 50000:
            print(f"Skipping {soustype_name} (> 50k threshold: {len(coords)})")
            continue
        if len(coords) < 2:
            print(f"Skipping {soustype_name} (< 2 threshold: {len(coords)})")
            continue
        """

        # Adjust the eps parameter for tighter clustering
        db = DBSCAN(eps=20/earth_radius, min_samples=2, algorithm='ball_tree', metric='haversine').fit(coords)

        # Offset cluster labels globally and assign to dataframe
        valid_geo_data['cluster'] = db.labels_ + cluster_counter

        # Store clustered data
        clustered_data_list.append(valid_geo_data)

        # Update cluster counter for global uniqueness
        cluster_counter = valid_geo_data['cluster'].max() + 1

    # Concatenate all clustered sous-types into a single dataframe
    clustered_data_full = pd.concat(clustered_data_list)

    # Output info
    print("Shape of clustered_data_full:", clustered_data_full.shape)
    print("Head of clustered_data_full with centroids:")
    print(clustered_data_full.head())

    return clustered_data_full

def explore_clusters(df, step):
    """
    Perform preliminary data exploration on the clustered data.
    """
    # Group by cluster and count the number of rows in each cluster
    cluster_counts = df.groupby('cluster').size().reset_index(name='count')

    # Sort the clusters by count in descending order
    cluster_counts_sorted = cluster_counts.sort_values(by='count', ascending=False)

    # Print the top clusters
    print(f"Top clusters by count after {step}:")
    print(cluster_counts_sorted.head(100))

    # Print the number of clusters
    num_clusters = cluster_counts_sorted.shape[0]
    print(f"Number of clusters after {step}: {num_clusters}")

    return cluster_counts_sorted

def split_large_clusters(df, max_cluster_size_m=20, min_points_to_split=2, max_subclusters=500):
    """
    For each cluster in the dataframe:
    - If it's large and spatially spread out, re-cluster it into smaller sub-clusters using KMeans.
    """
    cluster_offset = df['cluster'].max() + 1  # Start new cluster IDs after the current max

    for cluster_id, group in df.groupby('cluster'):
        if len(group) <= 1:
            continue  # Skip singleton clusters

        # Estimate bounding box distance (quick approximation)
        lat_range = group['latitude'].max() - group['latitude'].min()
        lon_range = group['longitude'].max() - group['longitude'].min()
        approx_dist = np.sqrt((lat_range * 111000) ** 2 + (lon_range * 85000) ** 2)
        if approx_dist < max_cluster_size_m:
            continue  # Already tight cluster

        # Compute max distance using Haversine for actual spread
        coords_rad = np.radians(group[['latitude', 'longitude']])
        dists = haversine_distances(coords_rad) * 6371000  # meters
        max_dist = dists.max()
        if max_dist <= max_cluster_size_m:
            continue  # Skip if still compact

        # Trigger sub-clustering only for large and spread out clusters
        if len(group) >= min_points_to_split and max_dist > 100:
            # Estimate and clamp number of sub-clusters
            n_subclusters = int(np.ceil(max_dist / max_cluster_size_m))
            n_subclusters = min(n_subclusters, len(group), max_subclusters)
            if n_subclusters >= len(group):
                continue  # Avoid 1-point-per-cluster edge case

            print(f"Splitting cluster {cluster_id} with {len(group)} points, max_dist={int(max_dist)}m → {n_subclusters} subclusters")

            # Run KMeans clustering on lat/lon directly
            km = MiniBatchKMeans(n_clusters=n_subclusters, batch_size=256, n_init='auto')
            sub_labels = km.fit_predict(group[['latitude', 'longitude']])

            # Offset subcluster IDs to preserve global uniqueness
            df.loc[group.index, 'cluster'] = sub_labels + cluster_offset
            cluster_offset += n_subclusters

    return df

# Example usage
if __name__ == "__main__":
    from pdb import set_trace as b
    import time
    tic = time.time()

    # Specify the sous-type for testing
    specific_soustype = "Trottoirs : Affaissement, trou, bosse, pavé arraché"  # Replace with the actual sous-type you want to test

    # Run clustering algorithm
    clustered_data = cluster_data_by_soustype('conseil-quartier', 'dans_ma_rue', 'feed_requetes_dmr', specific_soustype)
    print(f"Total elapsed time for clustering: {round(time.time()-tic, 2)} sec")

    # Perform preliminary data exploration
    cluster_counts_sorted = explore_clusters(clustered_data, "initial clustering")

    # Run sub-clustering if necessary
    clustered_data = split_large_clusters(clustered_data)

    # Re-explore clusters after sub-clustering
    cluster_counts_sorted_after_subclustering = explore_clusters(clustered_data, "sub-clustering")

    # Save the clustered data to a CSV file for plotting
    clustered_data.to_csv("clustered_data.csv", index=False)
