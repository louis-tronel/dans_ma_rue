import os
import csv
import json
import requests
from io import StringIO
from google.cloud import bigquery
from pdb import set_trace as b

# Only relevant when running locally
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/greg/playground/louis/service_account.json"

def fetch_from_api():
    """
    Fetches the 'Dans ma rue' dataset from OpenData Paris API and filters it as needed.
    Returns a list of dictionaries (rows).
    """
    endpoint = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/dans-ma-rue/exports/csv?where=conseilquartier='ALIGRE - GARE DE LYON'"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(endpoint, headers=headers, timeout=5)
        response.raise_for_status()
        print("Success:", response.status_code)
    except requests.exceptions.Timeout:
        print("Request timed out!")
        return []
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return []

    # Read CSV into a list of dictionaries
    csv_data = StringIO(response.text)
    reader = csv.DictReader(csv_data, delimiter=';')
    reader.fieldnames = [col.lstrip('\ufeff') for col in reader.fieldnames] if reader.fieldnames else []
    data = [row for row in reader]

    # Convert specific fields
    for row in data:
        row["code_postal"] = str(row.get("code_postal", ""))
        row["anneedecl"] = str(row.get("anneedecl", ""))
        row["datedecl"] = row.get("datedecl", "").replace("/", "-")  # Format date

    print(f"Total records retrieved from API: {len(data)}")
    return data

def fetch_from_bigquery(project_id=None, dataset_id=None, table_id=None):
    """
    Fetches existing 'id_dmr' values from a BigQuery table.
    Returns a set of known 'id_dmr' values.
    """
    client = bigquery.Client()

    query = f"SELECT id_dmr FROM `{project_id}.{dataset_id}.{table_id}`"
    
    try:
        query_job = client.query(query)
        rows = list(query_job)
        known_ids = {str(row["id_dmr"]) for row in rows}
        print(f"Total records retrieved from bigquery table: {len(known_ids)}")
        return known_ids
    except Exception as e:
        print("Error fetching data from BigQuery:", e)
        return set()

def upload_to_bigquery(data, project_id=None, dataset_id=None, table_id=None):
    """
    Uploads a list of dictionaries (new records) to a BigQuery table.
    """
    if not data:
        print("Skipping upload - No new records to insert.")
        return

    client = bigquery.Client()
    table_ref = client.dataset(dataset_id).table(table_id)

    try:
        job = client.insert_rows_json(table_ref, data)
        if job:
            print("Errors during upload:", job)
        else:
            print(f"Data successfully appended to {dataset_id}.{table_id}")
    except Exception as e:
        print("Error uploading to BigQuery:", e)


if __name__ == "__main__":

    # Get dataset from API
    data = fetch_from_api()

    # Get existing IDs from BigQuery
    known_ids = fetch_from_bigquery(
        project_id='conseil-quartier',
        dataset_id='dans_ma_rue', 
        table_id='feed_requetes_dmr'
    )

    # Filter out records already in BigQuery
    new_data = [row for row in data if row["id_dmr"] not in known_ids]
    print(f"{len(new_data)} records to append to table")

    # Upload new records to table
    upload_to_bigquery(
        new_data, 
        project_id='conseil-quartier', 
        dataset_id='dans_ma_rue', 
        table_id='feed_requetes_dmr'
    )

