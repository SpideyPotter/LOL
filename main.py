"""
League of Legends Match Analyzer
Main entry point for the application
"""
import os
from src.api_scraper import fetch_summoner_data, fetch_match_history, save_match_data

def main():
    print("League of Legends Match Analyzer")
    
    # Get API key and summoner name
    api_key = input("Enter your Riot API key: ")
    summoner_name = input("Enter summoner name: ")
    region = input("Enter region (e.g., na1, euw1, kr): ") or "na1"
    match_count = int(input("Number of matches to fetch (max 100): ") or "10")
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Fetch summoner data
    print(f"Fetching data for summoner: {summoner_name}")
    summoner_data = fetch_summoner_data(api_key, summoner_name, region)
    
    if not summoner_data:
        print("Failed to fetch summoner data. Please check your API key and summoner name.")
        return
    
    # Fetch match history
    print(f"Fetching match history for {summoner_name}...")
    match_data = fetch_match_history(api_key, summoner_data['puuid'], region, match_count)
    
    if not match_data:
        print("Failed to fetch match data.")
        return
    
    # Save match data to CSV
    output_file = "data/lol_match_data.csv"
    save_match_data(match_data, output_file)
    print(f"Match data saved to {output_file}")

if __name__ == "__main__":
    main()