"""
API Scraper for Riot Games API
Fetches summoner data and match history
"""
import requests
import pandas as pd
import time
import json

# Base URLs for different Riot API endpoints
REGION_ROUTING = {
    'na1': 'americas',
    'euw1': 'europe',
    'kr': 'asia',
    'br1': 'americas',
    'eun1': 'europe',
    'jp1': 'asia',
    'la1': 'americas',
    'la2': 'americas',
    'oc1': 'sea',
    'tr1': 'europe',
    'ru': 'europe',
    'ph2': 'sea',
    'sg2': 'sea',
    'th2': 'sea',
    'tw2': 'sea',
    'vn2': 'sea',
}

def fetch_summoner_data(api_key, summoner_name, region='na1'):
    """
    Fetch basic summoner data using the Riot API
    
    Args:
        api_key (str): Riot API key
        summoner_name (str): Summoner name to look up
        region (str): Region code (default: na1)
        
    Returns:
        dict: Summoner data or None if request failed
    """
    url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}"
    headers = {
        "X-Riot-Token": api_key
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching summoner data: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Status code: {e.response.status_code}")
            print(f"Response: {e.response.text}")
        return None

def fetch_match_history(api_key, puuid, region='na1', count=10):
    """
    Fetch match history for a summoner
    
    Args:
        api_key (str): Riot API key
        puuid (str): Player's PUUID from summoner data
        region (str): Region code (default: na1)
        count (int): Number of matches to fetch (default: 10)
        
    Returns:
        list: List of match data dictionaries
    """
    # Convert region to routing value
    routing = REGION_ROUTING.get(region, 'americas')
    
    # Get match IDs
    match_ids_url = f"https://{routing}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
    headers = {
        "X-Riot-Token": api_key
    }
    params = {
        "start": 0,
        "count": count
    }
    
    try:
        response = requests.get(match_ids_url, headers=headers, params=params)
        response.raise_for_status()
        match_ids = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching match IDs: {e}")
        return []
    
    # Fetch details for each match
    match_data_list = []
    for match_id in match_ids:
        match_url = f"https://{routing}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        
        try:
            response = requests.get(match_url, headers=headers)
            response.raise_for_status()
            match_data = response.json()
            
            # Process match data to extract relevant information
            processed_data = process_match_data(match_data, puuid)
            match_data_list.append(processed_data)
            
            # Sleep to avoid rate limiting
            time.sleep(1.2)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching match data for {match_id}: {e}")
            continue
    
    return match_data_list

def process_match_data(match_data, puuid):
    """
    Process raw match data to extract relevant information
    
    Args:
        match_data (dict): Raw match data from Riot API
        puuid (str): Player's PUUID to identify the player in the match
        
    Returns:
        dict: Processed match data with relevant fields
    """
    # Extract basic match info
    match_info = match_data.get('info', {})
    game_id = match_info.get('gameId', 0)
    game_duration = match_info.get('gameDuration', 0)
    game_mode = match_info.get('gameMode', '')
    game_type = match_info.get('gameType', '')
    
    # Find the player in the participants list
    player_data = {}
    for participant in match_info.get('participants', []):
        if participant.get('puuid') == puuid:
            player_data = {
                'champion': participant.get('championName', ''),
                'kills': participant.get('kills', 0),
                'deaths': participant.get('deaths', 0),
                'assists': participant.get('assists', 0),
                'win': participant.get('win', False),
                'position': participant.get('individualPosition', ''),
                'gold_earned': participant.get('goldEarned', 0),
                'damage_dealt': participant.get('totalDamageDealtToChampions', 0),
                'vision_score': participant.get('visionScore', 0),
                'cs': participant.get('totalMinionsKilled', 0) + participant.get('neutralMinionsKilled', 0),
            }
            break
    
    # Combine match info with player data
    return {
        'game_id': game_id,
        'game_duration': game_duration,
        'game_mode': game_mode,
        'game_type': game_type,
        'match_date': match_info.get('gameCreation', 0),
        **player_data
    }

def save_match_data(match_data_list, output_file):
    """
    Save match data to a CSV file
    
    Args:
        match_data_list (list): List of processed match data dictionaries
        output_file (str): Path to output CSV file
    """
    if not match_data_list:
        print("No match data to save")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(match_data_list)
    
    # Convert match date from milliseconds to datetime
    df['match_date'] = pd.to_datetime(df['match_date'], unit='ms')
    
    # Convert game duration from seconds to minutes
    df['game_duration_minutes'] = df['game_duration'] / 60
    
    # Calculate KDA
    df['kda'] = (df['kills'] + df['assists']) / df['deaths'].replace(0, 1)
    
    # Calculate CS per minute
    df['cs_per_min'] = df['cs'] / df['game_duration_minutes']
    
    # Save to CSV
    df.to_csv(output_file, index=False)