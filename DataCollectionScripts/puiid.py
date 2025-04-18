import requests
import time
import os
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
if not API_KEY:
    print("❌ Error: RIOT_API_KEY not found in .env file")
    exit(1)

# Allow region to be specified
region = os.getenv("REGION", "na1")
match_region_mapping = {
    "na1": "americas", "br1": "americas", "la1": "americas", "la2": "americas",
    "euw1": "europe", "eun1": "europe", "tr1": "europe", "ru": "europe",
    "kr": "asia", "jp1": "asia"
}
match_region = match_region_mapping.get(region, "americas")
headers = {"X-Riot-Token": API_KEY}

# Get Challenger players
url = f"https://{region}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5"
response = requests.get(url, headers=headers)

# Rate limiting variables
requests_made = 0
last_request_time = time.time()

if response.status_code == 200:
    data = response.json()
    entries = data.get("entries", [])
    
    entries.sort(key=lambda x: x.get("leaguePoints", 0), reverse=True)
    
    # Process all challenger players
    all_players = entries

    print(f"🔍 Fetching details for all {len(all_players)} challenger players in {region}...")

    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Use CSV format with headers for better data organization
    with open("data/all_challenger_puuids.csv", "w") as f:
        f.write("rank,name,puuid,league_points,wins,losses,win_rate\n")
        
        for i, entry in enumerate(all_players):
            summoner_id = entry.get("summonerId")
            league_points = entry.get("leaguePoints", 0)
            name = entry.get("summonerName", "Unknown")
            wins = entry.get("wins", 0)
            losses = entry.get("losses", 0)
            win_rate = round(wins / (wins + losses) * 100, 2) if (wins + losses) > 0 else 0

            # Show progress every 10 players
            if (i+1) % 10 == 0:
                print(f"Processing player {i+1}/{len(all_players)}...")

            if summoner_id:
                try:
                    summoner_url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}"
                    summoner_response = requests.get(summoner_url, headers=headers)
                    
                    # Check rate limit: If 100 requests have been made in the last 2 minutes, sleep
                    if requests_made >= 100:
                        time_diff = time.time() - last_request_time
                        if time_diff < 120:
                            sleep_time = 120 - time_diff
                            print(f"⏳ Sleeping for {sleep_time:.1f} seconds to avoid rate limit...")
                            time.sleep(sleep_time)
                        requests_made = 0  # Reset count after sleep
                        last_request_time = time.time()
                    
                    if summoner_response.status_code == 200:
                        summoner_data = summoner_response.json()
                        puuid = summoner_data.get("puuid")
                        
                        if puuid:
                            f.write(f"{i+1},{name},{puuid},{league_points},{wins},{losses},{win_rate}\n")
                            # Only print details for every 10th player to avoid console spam
                            if i % 10 == 0:
                                print(f"✅ #{i+1}: {name:<20} | {league_points:>4} LP | Win Rate: {win_rate:>5.1f}% | PUUID: {puuid[:15]}...")
                    else:
                        print(f"⚠️ Failed to get data for {name} - Status: {summoner_response.status_code}")
                    
                    # Rate limiting: respect 1.2 seconds between requests
                    requests_made += 1
                    time.sleep(1.2)  # sleep to avoid rate limits
                    
                except Exception as e:
                    print(f"❌ Error processing player {name}: {str(e)}")
                    continue

    print("\n✅ Done! All challenger player info saved to data/all_challenger_puuids.csv")
    
    # Print summary of top 10 players in a nice table format
    print("\n📊 TOP 10 CHALLENGER PLAYERS SUMMARY")
    print("=" * 70)
    print(f"{'Rank':<5}{'Player':<25}{'LP':<8}{'Win Rate':<12}{'W/L':<10}")
    print("-" * 70)
    
    for i, entry in enumerate(all_players[:10]):
        name = entry.get("summonerName", "Unknown")
        lp = entry.get("leaguePoints", 0)
        wins = entry.get("wins", 0)
        losses = entry.get("losses", 0)
        win_rate = round(wins / (wins + losses) * 100, 2) if (wins + losses) > 0 else 0
        print(f"{i+1:<5}{name:<25}{lp:<8}{win_rate:.1f}%{f' ({wins}/{losses})':<10}")
    
    print("=" * 70)
    print(f"Total players processed: {len(all_players)}")

else:
    print(f"❌ Failed to fetch challenger list: {response.status_code}")
    print(f"Response: {response.text}")