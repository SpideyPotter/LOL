import requests
API_KEY = "RGAPI-ff6528da-850d-410e-afe8-3d52bb241044"
region_routing = "americas"  # NA = americas, KR = asia, EUW = europe
puuid = "J9g7ZfcT5BsW_gkyeXZMonb7Kdbm4fJn2kfSCBUtcSMvfoMiaje8aVRDQHet6GHerYOhmfbAkFbfug"

url = f"https://{region_routing}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count=10"
headers = {"X-Riot-Token": API_KEY}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    match_ids = response.json()
    print("Recent Match IDs:")
    for match_id in match_ids:
        print(match_id)
else:
    print("Error fetching matches:", response.status_code)