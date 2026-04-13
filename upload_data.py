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

def trigger_view_refresh():
    """Calls the Supabase RPC function to recalculate all stats"""
    print("\n🚀 Triggering Materialized View refresh...")
    try:
        # Call the SQL function we created in Supabase
        supabase.rpc('refresh_all_ipl_views').execute()
        print("✅ All views refreshed successfully! Your app is now up to date.")
    except Exception as e:
        print(f"❌ Error refreshing views: {e}")

def run_sync():
    # --- STEP 1: UPLOAD DATA ---
    json_files = glob.glob(os.path.join('data', '*.json'))
    print(f"🚀 Found {len(json_files)} matches. Starting Upload...")

    for file in tqdm(json_files, desc="Processing Matches"):
        with open(file, 'r') as f:
            data = json.load(f)
        
        match_id = os.path.basename(file).split('.')[0]
        info = data.get('info', {})
        teams = info.get('teams', [None, None])
        
        match_data = {
            'match_id': match_id,
            'match_date': info.get('dates', [None])[0],
            'season': str(info.get('dates', [''])[0])[:4],
            'venue': info.get('venue'),
            'city': info.get('city'),
            'team1': teams[0],
            'team2': teams[1],
            'winner': info.get('outcome', {}).get('winner'),
            'player_of_match': info.get('player_of_match', [None])[0]
        }
        
        supabase.table('matches').upsert(match_data).execute()

        delivery_list = []
        seen_balls = set() 
        
        for inning_idx, inning in enumerate(data.get('innings', [])):
            bat_team = inning.get('team')
            bowl_team = teams[1] if teams[0] == bat_team else teams[0]
            
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
                supabase.table('deliveries').upsert(delivery_list).execute()
            except Exception as e:
                tqdm.write(f"⚠️ Error uploading match {match_id}: {e}")

    print("\n✅ Upload Complete! All data is in the database.")
    
    # --- STEP 2: REFRESH VIEWS ---
    # We call this inside run_sync so it happens after the for-loop finishes
    trigger_view_refresh()

if __name__ == "__main__":
    run_sync()