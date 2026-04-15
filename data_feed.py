import pandas as pd
from supabase import create_client
import os
from dotenv import load_dotenv

def get_flourish_csv():
    load_dotenv()
    supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
    
    # Fetch the Top 30 data
    res = supabase.table('view_top_30_batting_race').select("player", "team", "match_seq", "cumulative_runs").execute()
    df = pd.DataFrame(res.data)
    
    # Pivot the data into the 'Wide' format Flourish loves:
    # Rows: Player | Team
    # Columns: Match 1 | Match 2 | Match 3 ...
    wide_df = df.pivot(index=['player', 'team'], columns='match_seq', values='cumulative_runs').reset_index()
    
    # Return as CSV string
    return wide_df.to_csv(index=False)