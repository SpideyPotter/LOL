import requests
import time

API_KEY = "RGAPI-ff6528da-850d-410e-afe8-3d52bb241044"
region = "na1"  # Change to euw1, kr, etc. for other regions
headers = {"X-Riot-Token": API_KEY}

# Endpoint to get Challenger league in Solo Queue
url = f"https://{region}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    entries = data.get("entries", [])
    
    # Sort entries by league points (highest first)
    entries.sort(key=lambda x: x.get("leaguePoints", 0), reverse=True)
    
    print(f"Found {len(entries)} challenger players.")
    
    # Extract summoner IDs and puuids
    top_players = []
    for i, entry in enumerate(entries[:20]):  # Limit to first 20
        summoner_id = entry.get("summonerId")
        league_points = entry.get("leaguePoints", 0)
        
        if summoner_id:
            # Make API call to get summoner details to get puuid
            summoner_url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}"
            summoner_response = requests.get(summoner_url, headers=headers)
            
            if summoner_response.status_code == 200:
                summoner_data = summoner_response.json()
                puuid = summoner_data.get("puuid", "unknown")
                
                player_info = {
                    "rank": i+1,
                    "lp": league_points,
                    "puuid": puuid,
                    "summoner_id": summoner_id
                }
                
                top_players.append(player_info)
                print(f"Player {i+1}: LP: {league_points}, PUUID: {puuid[:15]}...")
            else:
                print(f"Failed to get summoner details for ID {summoner_id[:10]}... Status: {summoner_response.status_code}")
            
            # Sleep to avoid rate limiting
            time.sleep(1.2)
    
    print(f"✅ Retrieved {len(top_players)} top challenger players!")
    
    # Optional: Save to file with league points and puuid
    with open("challenger_players.txt", "w") as f:
        for player in top_players:
            f.write(f"Rank {player['rank']}: LP {player['lp']}, PUUID: {player['puuid']}\n")
    
    print(f"Player data saved to challenger_players.txt")
    
    # Optional: Get match history for the top player
    if top_players:
        top_player = top_players[0]
        puuid = top_player["puuid"]
        
        print(f"\nFetching recent matches for top player (Rank 1, LP: {top_player['lp']})...")
        
        # Get match IDs for the top player
        match_region = "americas"  # Adjust based on your region
        matches_url = f"https://{match_region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=5"
        matches_response = requests.get(matches_url, headers=headers)
        
        if matches_response.status_code == 200:
            match_ids = matches_response.json()
            print(f"Found {len(match_ids)} recent matches for top player")
            
            # Print match IDs
            for i, match_id in enumerate(match_ids):
                print(f"Match {i+1}: {match_id}")
        else:
            print(f"Failed to get matches: {matches_response.status_code}")

else:
    print(f"❌ Failed to fetch leaderboard: {response.status_code}")
    print(f"Response: {response.text}")