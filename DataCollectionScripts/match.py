import requests
import os
import time
import csv
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
if not API_KEY:
    print("❌ Error: RIOT_API_KEY not found in .env file")
    exit(1)

headers = {"X-Riot-Token": API_KEY}

# Read region from env or use default
region = os.getenv("REGION", "na1")
match_region_mapping = {
    "na1": "americas", "br1": "americas", "la1": "americas", "la2": "americas",
    "euw1": "europe", "eun1": "europe", "tr1": "europe", "ru": "europe",
    "kr": "asia", "jp1": "asia"
}
region_routing = match_region_mapping.get(region, "americas")  # for match-v5

# Input and output files
# Use relative paths from script location
input_path = "data/all_challenger_puuids.csv"
output_path = "data/player_match_ids.csv"
# Rate limiting variables
requests_made = 0
last_request_time = time.time()

# Check if input file exists
if not os.path.exists(input_path):
    print(f"❌ Error: Input file {input_path} not found")
    print("Please run the puiid.py script first to generate the challenger player data")
    exit(1)

# Read player data from CSV
players = []
try:
    with open(input_path, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            players.append({
                "rank": row.get("rank", ""),
                "name": row.get("name", "Unknown"),
                "puuid": row.get("puuid", ""),
                "league_points": row.get("league_points", "0")
            })
    print(f"✅ Loaded {len(players)} players from {input_path}")
except Exception as e:
    print(f"❌ Error reading input file: {str(e)}")
    exit(1)

# Write header to output file
with open(output_path, "w") as f:
    f.write("rank,name,league_points,match_ids\n")

    for i, player in enumerate(players):
        name = player["name"]
        puuid = player["puuid"]
        rank = player["rank"]
        lp = player["league_points"]
        
        # Show progress every 10 players
        if (i+1) % 10 == 0:
            print(f"Processing player {i+1}/{len(players)}...")
        
        if not puuid:
            print(f"⚠️ Skipping {name} - No PUUID available")
            continue
            
        try:
            # Check rate limit
            if requests_made >= 100:
                time_diff = time.time() - last_request_time
                if time_diff < 120:
                    sleep_time = 120 - time_diff
                    print(f"⏳ Sleeping for {sleep_time:.1f} seconds to avoid rate limit...")
                    time.sleep(sleep_time)
                requests_made = 0
                last_request_time = time.time()
                
            # Fetch match IDs
            url = f"https://{region_routing}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
            params = {"count": 10, "queue": 420, "type": "ranked"}  # 420 = Ranked Solo 5v5
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                match_ids = response.json()
                # Write to CSV: rank, name, league_points, match_ids (comma-separated)
                match_ids_str = ",".join(match_ids)
                f.write(f"{rank},{name},{lp},\"{match_ids_str}\"\n")
                
                # Only print details for every 10th player to avoid console spam
                if i % 10 == 0:
                    print(f"✅ #{rank}: {name:<20} | {lp:>4} LP | Matches: {len(match_ids)}")
            else:
                print(f"❌ Failed for {name} | Status: {response.status_code}")
                if response.status_code == 429:
                    print("Rate limit exceeded. Sleeping for 2 minutes...")
                    time.sleep(120)
                    
            # Rate limiting
            requests_made += 1
            time.sleep(1.2)  # Prevent hitting rate limits
            
        except Exception as e:
            print(f"❌ Error processing {name}: {str(e)}")
            continue

print(f"\n✅ All match data saved to {output_path}")

# Print summary
print("\n📊 MATCH DATA COLLECTION SUMMARY")
print("=" * 70)
print(f"Total players processed: {len(players)}")
print(f"Data saved to: {output_path}")
print("=" * 70)