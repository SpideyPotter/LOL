import requests
import time
import os
import json
import csv
from dotenv import load_dotenv
from datetime import datetime

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
if not API_KEY:
    print("❌ Error: RIOT_API_KEY not found in .env file")
    exit(1)

# Read region from env or use default
region = os.getenv("REGION", "na1")
match_region_mapping = {
    "na1": "americas", "br1": "americas", "la1": "americas", "la2": "americas",
    "euw1": "europe", "eun1": "europe", "tr1": "europe", "ru": "europe",
    "kr": "asia", "jp1": "asia"
}
region_routing = match_region_mapping.get(region, "americas")

headers = {"X-Riot-Token": API_KEY}

# File paths
input_path = "data/player_match_ids.csv"
output_folder = "data/match_data"
# Rate limiting variables
requests_made = 0
last_request_time = time.time()
MAX_REQUESTS = 100
RATE_LIMIT_WINDOW = 120  # 2 minutes

# Make sure output folder exists
os.makedirs(output_folder, exist_ok=True)

# Create player-specific folders
player_folder = os.path.join(output_folder, "by_player")
os.makedirs(player_folder, exist_ok=True)

# Create a folder for all matches
matches_folder = os.path.join(output_folder, "all_matches")
os.makedirs(matches_folder, exist_ok=True)

# Check if input file exists
if not os.path.exists(input_path):
    print(f"❌ Error: Input file {input_path} not found")
    print("Please run the match.py script first to generate the player match IDs")
    exit(1)

# Read match IDs from CSV
player_matches = []
try:
    with open(input_path, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # The match_ids column contains a comma-separated list of match IDs
            match_ids_str = row.get("match_ids", "").strip('"')
            match_ids = match_ids_str.split(",") if match_ids_str else []
            
            if match_ids:
                player_matches.append({
                    "rank": row.get("rank", ""),
                    "name": row.get("name", "Unknown"),
                    "league_points": row.get("league_points", "0"),
                    "match_ids": match_ids
                })
    
    print(f"✅ Loaded match data for {len(player_matches)} players from {input_path}")
except Exception as e:
    print(f"❌ Error reading input file: {str(e)}")
    exit(1)

# Create a set to track unique match IDs (to avoid duplicates)
all_match_ids = set()
for player in player_matches:
    for match_id in player["match_ids"]:
        if match_id:  # Skip empty strings
            all_match_ids.add(match_id)

print(f"🔍 Found {len(all_match_ids)} unique match IDs to process")

# Create a log file to track progress
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(output_folder, f"match_data_log_{timestamp}.txt")

with open(log_file, "w") as log:
    log.write(f"Match data collection started at {datetime.now()}\n")
    log.write(f"Total unique matches to process: {len(all_match_ids)}\n\n")
    
    # Process each player's matches
    for player_idx, player in enumerate(player_matches):
        player_name = player["name"]
        player_rank = player["rank"]
        match_ids = player["match_ids"]
        
        # Create a folder for this player
        safe_name = "".join(c if c.isalnum() else "_" for c in player_name)
        player_match_folder = os.path.join(player_folder, f"{player_rank}_{safe_name}")
        os.makedirs(player_match_folder, exist_ok=True)
        
        log.write(f"Processing player {player_idx+1}/{len(player_matches)}: {player_name} (Rank {player_rank})\n")
        print(f"\nProcessing player {player_idx+1}/{len(player_matches)}: {player_name} (Rank {player_rank})")
        
        # Process each match for this player
        for match_idx, match_id in enumerate(match_ids):
            if not match_id:  # Skip empty match IDs
                continue
                
            # Check if we already have this match data
            match_file_path = os.path.join(matches_folder, f"{match_id}.json")
            if os.path.exists(match_file_path):
                # Create a symlink to the existing match data in the player's folder
                player_match_path = os.path.join(player_match_folder, f"{match_id}.json")
                if not os.path.exists(player_match_path):
                    os.symlink(match_file_path, player_match_path)
                
                log.write(f"  Match {match_idx+1}/{len(match_ids)}: {match_id} - Already exists, created link\n")
                continue
            
            # Check rate limit
            if requests_made >= MAX_REQUESTS:
                time_diff = time.time() - last_request_time
                if time_diff < RATE_LIMIT_WINDOW:
                    sleep_time = RATE_LIMIT_WINDOW - time_diff
                    log.write(f"  Rate limit reached. Sleeping for {sleep_time:.1f} seconds\n")
                    print(f"⏳ Rate limit reached. Sleeping for {sleep_time:.1f} seconds...")
                    time.sleep(sleep_time)
                requests_made = 0
                last_request_time = time.time()
            
            # Fetch match data
            url = f"https://{region_routing}.api.riotgames.com/lol/match/v5/matches/{match_id}"
            try:
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    match_data = response.json()
                    
                    # Save to all_matches folder
                    with open(match_file_path, "w") as f:
                        json.dump(match_data, f, indent=2)
                    
                    # Create a symlink in the player's folder
                    player_match_path = os.path.join(player_match_folder, f"{match_id}.json")
                    if not os.path.exists(player_match_path):
                        os.symlink(match_file_path, player_match_path)
                    
                    log.write(f"  Match {match_idx+1}/{len(match_ids)}: {match_id} - ✅ Saved\n")
                    print(f"  Match {match_idx+1}/{len(match_ids)}: {match_id} - ✅ Saved")
                else:
                    log.write(f"  Match {match_idx+1}/{len(match_ids)}: {match_id} - ❌ Failed: Status {response.status_code}\n")
                    print(f"  Match {match_idx+1}/{len(match_ids)}: {match_id} - ❌ Failed: Status {response.status_code}")
                    
                    if response.status_code == 429:
                        retry_after = int(response.headers.get('Retry-After', 10))
                        log.write(f"  Rate limit exceeded. Sleeping for {retry_after} seconds\n")
                        print(f"⏳ Rate limit exceeded. Sleeping for {retry_after} seconds...")
                        time.sleep(retry_after)
            
            except Exception as e:
                log.write(f"  Match {match_idx+1}/{len(match_ids)}: {match_id} - ❌ Error: {str(e)}\n")
                print(f"  Match {match_idx+1}/{len(match_ids)}: {match_id} - ❌ Error: {str(e)}")
            
            # Rate limiting
            requests_made += 1
            time.sleep(1.2)  # Respect Riot's rate limit
    
    log.write(f"\nMatch data collection completed at {datetime.now()}\n")
    log.write(f"Total players processed: {len(player_matches)}\n")
    log.write(f"Total unique matches processed: {len(all_match_ids)}\n")

print("\n✅ Match data collection complete!")
print(f"📊 Summary:")
print(f"  - Processed {len(player_matches)} players")
print(f"  - Collected data for {len(all_match_ids)} unique matches")
print(f"  - Data saved to {output_folder}")
print(f"  - Log file: {log_file}")