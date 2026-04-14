import streamlit as st

def inject_custom_css():
    """Injects professional Glassmorphism CSS into the app."""
    st.markdown("""
        <style>
        /* Main App Background */
        .stApp {
            background: radial-gradient(circle at top right, #1e272e, #0f141a);
            color: #ffffff;
        }

        /* Glassmorphism Containers */
        [data-testid="stVerticalBlock"] > div > div > div[data-testid="stVerticalBlock"] {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 25px;
            backdrop-filter: blur(10px);
            margin-bottom: 20px;
            transition: transform 0.3s ease;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #0f141a !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }

        /* Metrics & Stat Styling */
        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            border-left: 4px solid #F1C40F;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 15px;
        }

        .stat-label {
            font-size: 0.75rem;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 5px;
        }

        .stat-value {
            font-size: 1.8rem;
            font-weight: 800;
            color: #ffffff;
        }

        /* Custom Header Font */
        h1, h2, h3 {
            font-family: 'Inter', sans-serif;
            font-weight: 700 !important;
            letter-spacing: -0.5px;
        }
        
        /* Smooth divider */
        hr {
            margin: 2em 0;
            border: 0;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)

def get_team_color(team_name):
    """Returns a hex color code based on the IPL team name."""
    colors = {
        "Chennai Super Kings": "#F1C40F", # Yellow
        "Mumbai Indians": "#004BA0",      # Blue
        "Royal Challengers Bengaluru": "#EC1C24", # Red
        "Kolkata Knight Riders": "#2E0854", # Purple
        "Delhi Capitals": "#00008B",      # Dark Blue
        "Rajasthan Royals": "#EA1A85",    # Pink
        "Punjab Kings": "#DD1F2D",        # Red/Silver
        "Sunrisers Hyderabad": "#FF822E", # Orange
        "Lucknow Super Giants": "#0057E2", # Cyan/Blue
        "Gujarat Titans": "#1B2133",      # Navy
    }
    return colors.get(team_name, "#888888") # Default Grey

def styled_stat_card(label, value, team_name=None):
    """Renders a beautiful centered stat card."""
    border_color = get_team_color(team_name) if team_name else "#F1C40F"
    st.markdown(f"""
        <div class="stat-card" style="border-left-color: {border_color};">
            <p class="stat-label">{label}</p>
            <p class="stat-value">{value}</p>
        </div>
    """, unsafe_allow_html=True)