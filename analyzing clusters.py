import pandas as pd

def analyze_cluster_sizes(df):
    """
    Analyze the number of clusters by the number of records they have, categorized into bins.
    """
    # Group by cluster and count the number of rows in each cluster
    cluster_counts = df.groupby('cluster').size().reset_index(name='count')

    # Define bins for cluster sizes
    bins = [0, 1, 2, 3, 10, 50, float('inf')]
    labels = ['0-1', '1-2', '2-3', '3-10', '10-50', '>50']

    # Categorize cluster sizes into bins
    cluster_counts['bin'] = pd.cut(cluster_counts['count'], bins=bins, labels=labels, right=False)

    # Count the number of clusters in each bin
    cluster_size_distribution = cluster_counts.groupby('bin').size().reset_index(name='cluster_count')

    # Print the distribution of cluster sizes
    print("Distribution of cluster sizes:")
    print(cluster_size_distribution)

    return cluster_size_distribution

# Example usage
if __name__ == "__main__":
    # Load clustered data from the CSV file
    clustered_data = pd.read_csv("clustered_data.csv")

    # Analyze cluster sizes
    cluster_size_distribution = analyze_cluster_sizes(clustered_data)
