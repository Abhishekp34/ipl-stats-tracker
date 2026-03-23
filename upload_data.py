import os
import json
import glob
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
from tqdm import tqdm  # <-- The new progress bar library

# 1. Connect to Supabase securely
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# 2. Find all JSON files in the 'data' folder
# Using os.path.join ensures this works on Mac, Windows, and Linux
search_path = os.path.join('data', '*.json')
json_files = glob.glob(search_path)
print(f"Found {len(json_files)} matches to process.")

# 3. Wrap the loop in tqdm() to generate the progress bar
for file in tqdm(json_files, desc="Uploading Matches", unit="match"):
    with open(file, 'r') as f:
        data = json.load(f)
        
    # Extract just the filename (e.g., '335982') without the 'data/' folder path
    base_name = os.path.basename(file)
    match_id = base_name.split('.')[0]
    
    info = data.get('info', {})
    teams = info.get('teams', [None, None])
    
    # --- PROCESS MATCH DATA ---
    match_data = {
        'match_id': match_id,
        'match_date': info.get('dates', [None])[0],
        'season': info.get('season') or str(info.get('dates', [''])[0])[:4],
        'city': info.get('city'),
        'venue': info.get('venue'),
        'team1': teams[0] if len(teams) > 0 else None,
        'team2': teams[1] if len(teams) > 1 else None,
        'toss_winner': info.get('toss', {}).get('winner'),
        'toss_decision': info.get('toss', {}).get('decision'),
        'winner': info.get('outcome', {}).get('winner'),
        'result_type': info.get('outcome', {}).get('result'),
        'result_margin': info.get('outcome', {}).get('by', {}).get('runs') or info.get('outcome', {}).get('by', {}).get('wickets'),
        'player_of_match': info.get('player_of_match', [None])[0]
    }
    
    # Upload Match to Supabase
    try:
        supabase.table('matches').upsert(match_data).execute()
    except Exception as e:
        # tqdm.write() is used instead of print() so it doesn't break the visual progress bar
        tqdm.write(f"Error uploading match {match_id}: {e}")
        continue 

    # --- PROCESS BALL-BY-BALL DATA ---
    delivery_list = []
    for inning_idx, inning in enumerate(data.get('innings', [])):
        batting_team = inning.get('team')
        bowling_team = teams[1] if teams[0] == batting_team else teams[0]
        
        for over in inning.get('overs', []):
            over_num = over.get('over')
            
            for ball_idx, delivery in enumerate(over.get('deliveries', [])):
                runs_info = delivery.get('runs', {})
                wicket_info = delivery.get('wickets', [{}])[0] if 'wickets' in delivery else {}
                
                delivery_list.append({
                    'match_id': match_id,
                    'inning': inning_idx + 1,
                    'over': over_num,
                    'ball': ball_idx + 1,
                    'batting_team': batting_team,
                    'bowling_team': bowling_team,
                    'batter': delivery.get('batter'),
                    'bowler': delivery.get('bowler'),
                    'non_striker': delivery.get('non_striker'),
                    'runs_batter': runs_info.get('batter', 0),
                    'runs_extras': runs_info.get('extras', 0),
                    'runs_total': runs_info.get('total', 0),
                    'wicket_type': wicket_info.get('kind'),
                    'player_out': wicket_info.get('player_out')
                })
    
    # Upload Deliveries in bulk for this match
    if delivery_list:
        try:
             supabase.table('deliveries').upsert(delivery_list).execute()
        except Exception as e:
             tqdm.write(f"Error uploading deliveries for {match_id}: {e}")

print("✅ All matches uploaded successfully!")