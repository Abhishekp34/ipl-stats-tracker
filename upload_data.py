import os
import json
import glob
from supabase import create_client, Client
from dotenv import load_dotenv
from tqdm import tqdm

# 1. SETUP
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def standardize_team_name(name, match_date):
    """
    Standardizes team names based on historical context.
    Handles the 'DC' paradox and name changes (Bangalore -> Bengaluru).
    """
    if not name:
        return name
    
    name = name.strip()
    year = int(str(match_date)[:4]) if match_date else 0

    # 1. Handle the "DC" Paradox
    # Deccan Chargers (2008-2012) vs Delhi Capitals (2019-Present)
    if name == "DC" or name == "Deccan Chargers":
        if year <= 2012:
            return "Deccan Chargers"
        else:
            return "Delhi Capitals"

    # 2. Map other variations to your 'Master' names
    mapping = {
        'Delhi Daredevils': 'Delhi Capitals',
        'Kings XI Punjab': 'Punjab Kings',
        'KXIP': 'Punjab Kings',
        'Royal Challengers Bangalore': 'Royal Challengers Bengaluru',
        'R C Bangalore': 'Royal Challengers Bengaluru',
        'RCB': 'Royal Challengers Bengaluru',
        'Rising Pune Supergiants': 'Rising Pune Supergiant',
        'Rising Pune Supergiant': 'Rising Pune Supergiant',
        'Pune Warriors India': 'Pune Warriors'
    }
    
    return mapping.get(name, name)

def trigger_view_refresh():
    """Calls the Supabase RPC function to recalculate all stats"""
    print("\n🚀 Triggering Materialized View refresh...")
    try:
        supabase.rpc('refresh_all_ipl_views').execute()
        print("✅ All views refreshed successfully! Your app is now up to date.")
    except Exception as e:
        print(f"❌ Error refreshing views: {e}")

def run_sync():
    json_files = glob.glob(os.path.join('data', '*.json'))
    print(f"🚀 Found {len(json_files)} matches. Starting Upload...")

    for file in tqdm(json_files, desc="Processing Matches"):
        with open(file, 'r') as f:
            data = json.load(f)
        
        match_id = os.path.basename(file).split('.')[0]
        info = data.get('info', {})
        match_date = info.get('dates', [None])[0]
        
        # Standardize teams at the start
        raw_teams = info.get('teams', [None, None])
        team1 = standardize_team_name(raw_teams[0], match_date)
        team2 = standardize_team_name(raw_teams[1], match_date)
        winner = standardize_team_name(info.get('outcome', {}).get('winner'), match_date)
        
        match_data = {
            'match_id': match_id,
            'match_date': match_date,
            'season': str(match_date)[:4] if match_date else '',
            'venue': info.get('venue'),
            'city': info.get('city'),
            'team1': team1,
            'team2': team2,
            'winner': winner,
            'player_of_match': info.get('player_of_match', [None])[0]
        }
        
        supabase.table('matches').upsert(match_data).execute()

        delivery_list = []
        seen_balls = set() 
        
        for inning_idx, inning in enumerate(data.get('innings', [])):
            # Standardize batting and bowling teams for every ball
            raw_bat_team = inning.get('team')
            bat_team = standardize_team_name(raw_bat_team, match_date)
            bowl_team = team2 if team1 == bat_team else team1
            
            for over_data in inning.get('overs', []):
                current_over = over_data.get('over')
                
                for ball_idx, delivery in enumerate(over_data.get('deliveries', [])):
                    ball_id = (inning_idx + 1, current_over, ball_idx + 1)
                    
                    if ball_id in seen_balls:
                        continue 
                    seen_balls.add(ball_id)
                    
                    runs = delivery.get('runs', {})
                    wickets = delivery.get('wickets', [{}])[0] if 'wickets' in delivery else {}
                    extras = delivery.get('extras', {})
                    
                    delivery_list.append({
                        'match_id': match_id,
                        'inning': inning_idx + 1,
                        'over': current_over,
                        'ball': ball_idx + 1,
                        'batting_team': bat_team,
                        'bowling_team': bowl_team,
                        'batter': delivery.get('batter'),
                        'bowler': delivery.get('bowler'),
                        'non_striker': delivery.get('non_striker'),
                        'runs_batter': runs.get('batter', 0),
                        'runs_extras': runs.get('extras', 0),
                        'runs_total': runs.get('total', 0),
                        'extra_type': next(iter(extras)) if extras else None,
                        'wicket_type': wickets.get('kind'),
                        'player_out': wickets.get('player_out')
                    })
        
        if delivery_list:
            try:
                # Using 1000-row chunks for large matches (optional but safer for Supabase limits)
                for i in range(0, len(delivery_list), 1000):
                    supabase.table('deliveries').upsert(delivery_list[i:i+1000]).execute()
            except Exception as e:
                tqdm.write(f"⚠️ Error uploading match {match_id}: {e}")

    print("\n✅ Upload Complete! All data is in the database.")
    trigger_view_refresh()

if __name__ == "__main__":
    run_sync()