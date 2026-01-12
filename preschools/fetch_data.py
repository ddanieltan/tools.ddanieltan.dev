# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests",
# ]
# ///
import requests
import json
import os
import time

def fetch_geojson():
    print("Fetching GeoJSON...")
    datasetId = "d_61eefab99958fd70e6aab17320a71f1c"
    poll_url = f"https://api-open.data.gov.sg/v1/public/api/datasets/{datasetId}/poll-download"
    
    resp = requests.get(poll_url)
    resp.raise_for_status()
    data = resp.json()
    
    if data['code'] != 0:
        raise Exception(f"API Error: {data['errMsg']}")
        
    download_url = data['data']['url']
    print(f"Downloading GeoJSON from S3...")
    geo_resp = requests.get(download_url)
    geo_resp.raise_for_status()
    
    return geo_resp.json()

def fetch_listings():
    print("Fetching Listings...")
    datasetId = "d_696c994c50745b079b3684f0e90ffc53"
    base_url = "https://data.gov.sg/api/action/datastore_search"
    
    all_records = []
    limit = 500
    offset = 0
    
    while True:
        print(f"Fetching listings offset={offset}...")
        params = {
            "resource_id": datasetId,
            "limit": limit,
            "offset": offset
        }
        resp = requests.get(base_url, params=params)
        resp.raise_for_status()
        data = resp.json()
        
        records = data['result']['records']
        if not records:
            break
            
        all_records.extend(records)
        offset += limit
        
        # Safety break
        if len(all_records) > 10000:
            print("Warning: Reached 10,000 records limit, stopping.")
            break
            
        # Optional: Sleep to be nice to the API
        time.sleep(0.5)
        
    print(f"Total listings fetched: {len(all_records)}")
    return all_records

def main():
    try:
        # Ensure directory exists (current dir)
        
        geo_data = fetch_geojson()
        with open('preschools.geojson', 'w') as f:
            json.dump(geo_data, f)
        print("Saved preschools.geojson")
        
        listings_data = fetch_listings()
        with open('listings.json', 'w') as f:
            json.dump(listings_data, f)
        print("Saved listings.json")
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
