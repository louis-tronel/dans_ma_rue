def create_clustering_table(clustered_data, project_id, dataset_id, new_table_id):
    """
    Create a new table in BigQuery with clustering data.
    """
    client = bigquery.Client(project=project_id)
    dataset_ref = client.dataset(dataset_id)
    table_ref = dataset_ref.table(new_table_id)

    # Select only the necessary columns for the new table
    clustering_data = clustered_data[['id_dmr', 'cluster', 'centroid_latitude', 'centroid_longitude']]

    # Configure the load job
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",  # Overwrite the table if it exists
    )

    # Load the DataFrame to BigQuery
    load_job = client.load_table_from_dataframe(clustering_data, table_ref, job_config=job_config)
    load_job.result()  # Wait for the job to complete

    print(f"Clustering data uploaded to new table {dataset_id}.{new_table_id}")

# Example usage
create_clustering_table(clustered_data, 'conseil-quartier', 'dans_ma_rue', 'clustering_data')