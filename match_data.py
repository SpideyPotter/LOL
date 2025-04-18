import requests
import time
import os
import json
API_KEY = "RGAPI-ff6528da-850d-410e-afe8-3d52bb241044"
region_routing = "americas"
match_ids = [
    "NA1_5266048243",
    "NA1_5266012555",
    "NA1_5265969188",
    "NA1_5265933196",
    "NA1_5265910489",
    "NA1_5265875594",
    "NA1_5265839260",
    "NA1_5265781357",
    "NA1_5265748138",
    "NA1_5263238906"
]

headers = {"X-Riot-Token": API_KEY}
output_folder = "match_data"

# Make sure output folder exists
os.makedirs(output_folder, exist_ok=True)

for match_id in match_ids:
    url = f"https://{region_routing}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        match_data = response.json()
        with open(f"{output_folder}/{match_id}.json", "w") as f:
            json.dump(match_data, f, indent=2)
        print(f"✅ Saved: {match_id}.json")
    else:
        print(f"❌ Failed to fetch {match_id}: Status {response.status_code}")

    time.sleep(1.2)  # Respect Riot's rate limit