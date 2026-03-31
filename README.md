# 🏏 IPL Stats Tracker (2008 - 2025)

An interactive, high-performance web application built with **Streamlit** and **Supabase** that provides deep insights into Indian Premier League history. This project leverages Materialized Views and advanced SQL to deliver real-time leaderboards and animated player progression races.

## 🚀 Features

### 1. 🏃 All-Time Player Race (New!)
* **Animated Bar Chart Race:** Watch the top 10 run-scorers and wicket-takers evolve match-by-match from 2008 to 2024.
* **Smooth Transitions:** Optimized using CSS-style transitions and `st.empty` containers to ensure bars slide past each other during rank changes.
* **Dedicated Player Colors:** Top legends (Kohli, Dhoni, Rohit, etc.) have fixed colors for easy tracking.
* **Interactive Timeline:** Manually seek to any of the 1,100+ matches or hit "Play" for an automated experience.

### 2. 🏆 Dynamic Leaderboards
* **Real-time Rankings:** Global batting and bowling master tables updated via Supabase Materialized Views.
* **Podium Highlights:** Visual "Top 3" cards with key metrics like Average, Strike Rate, and Economy.
* **Smart Search:** Instantly filter thousands of players to find specific career stats.

### 3. 🏟️ Venue & Rivalry Insights
* **Standardized Data:** Cleaned venue and team names (e.g., "Kings XI Punjab" → "Punjab Kings") for consistent historical analysis.
* **Head-to-Head:** Detailed team rivalry stats including top performers in specific matchups.

---

## 🛠️ Tech Stack

* **Frontend:** [Streamlit](https://streamlit.io/) (Python)
* **Database:** [Supabase](https://supabase.com/) (PostgreSQL)
* **Visualization:** [Plotly Express](https://plotly.com/python/plotly-express/)
* **Data Processing:** Python (Pandas), SQL (Window Functions, Materialized Views)

---

## 🏗️ Database Architecture

The project uses highly optimized **Materialized Views** to handle heavy computations (like cumulative sums and dense ranking) on the database side, ensuring the UI remains lightning-fast.

Key Views:
* `view_batter_master`: Aggregated career batting statistics.
* `view_player_race_matrix`: Array-based progression for every player.
* `view_top_30_batting_race`: Un-nested, ranked history for the animation engine.

---

## 💻 Local Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/your-username/ipl-stats-tracker.git](https://github.com/your-username/ipl-stats-tracker.git)
   cd ipl-stats-tracker
   ```

2. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` or `.streamlit/secrets.toml` file with your Supabase credentials:
   ```env
   SUPABASE_URL = "your_supabase_url"
   SUPABASE_KEY = "your_supabase_anon_key"
   ```

5. **Run the App:**
   ```bash
   streamlit run Home.py
   ```

---

## 📈 Roadmap
- [x] Animated Player Race
- [x] Global Leaderboards
- [ ] Toss Impact Analysis
- [ ] Win Probability Predictor
- [ ] Player Comparison Tool

---
