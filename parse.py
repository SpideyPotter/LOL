import json
import pandas as pd

# Load the JSON match file
with open("match_data/NA1_5263238906.json", "r") as f:
    match_data = json.load(f)

participants = match_data["info"]["participants"]
match_id = match_data["metadata"]["matchId"]

rows = []
for p in participants:
    rows.append({
        "match_id": match_id,
        "summoner_name": p.get("summonerName", "unknown"),
        "puuid": p["puuid"],
        "champion": p["championName"],
        "kills": p["kills"],
        "deaths": p["deaths"],
        "assists": p["assists"],
        "win": p["win"],
        "role": p["teamPosition"],
        "team_id": p["teamId"]
    })

# Convert to DataFrame
df = pd.DataFrame(rows)
df.to_csv("parsed_match_data.csv", index=False)
print("✅ Saved parsed match data to parsed_match_data.csv")