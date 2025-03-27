import folium
import pandas as pd
import random

def get_random_color():
    """
    Generate a random color in hexadecimal format.
    """
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

def plot_clusters_on_map(df, num_clusters_to_plot=10, output_file="clusters_map.html"):
    """
    Plot clusters on a map using folium with different colors for each cluster.
    """
    # Get the top clusters by count
    top_clusters = df['cluster'].value_counts().index[:num_clusters_to_plot]

    # Create a map centered around the mean latitude and longitude of the data
    map_center = [df['latitude'].mean(), df['longitude'].mean()]
    m = folium.Map(location=map_center, zoom_start=12)

    # Assign a random color to each cluster
    cluster_colors = {cluster_id: get_random_color() for cluster_id in top_clusters}

    # Add clusters to the map
    for cluster_id in top_clusters:
        cluster_data = df[df['cluster'] == cluster_id]
        color = cluster_colors[cluster_id]

        folium.Marker(
            location=[cluster_data['latitude'].mean(), cluster_data['longitude'].mean()],
            popup=f"Cluster ID: {cluster_id} with {len(cluster_data)} points",
            icon=folium.DivIcon(html=f'<div style="font-size: 12pt; color:{color}">{cluster_id}</div>')
        ).add_to(m)

        # Add points to the map
        for _, point in cluster_data.iterrows():
            folium.CircleMarker(
                location=[point['latitude'], point['longitude']],
                radius=5,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.6
            ).add_to(m)

    # Save the map to an HTML file
    m.save(output_file)
    print(f"Map saved as {output_file}")

# Example usage
if __name__ == "__main__":
    # Load clustered data from the CSV file saved by the clustering script
    clustered_data = pd.read_csv("clustered_data.csv")

    # Plot clusters on a map
    plot_clusters_on_map(clustered_data, num_clusters_to_plot=10)