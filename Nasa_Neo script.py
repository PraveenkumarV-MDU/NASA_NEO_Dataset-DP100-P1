import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# ----------------------------
# 1. Streamlit basic setup
# ----------------------------
st.set_page_config(
    page_title="NASA NEO Tracker",
    page_icon="🚀",
    layout='wide',
    initial_sidebar_state="expanded"
)

# ----------------------------
# 2. Custom CSS
# ----------------------------
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72, #2a5298);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        color: white;
        text-align: center;
    }
    
    .query-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin: 1rem 0;
    }
    
    .filter-section {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .stSelectbox > div > div {
        background-color: #e3f2fd;
        border-radius: 5px;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #2c3e50, #34495e);
    }
    
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)
# -------------------------------------------------------------------
# Session state: selected query + filter defaults
# -------------------------------------------------------------------
if "selected_query" not in st.session_state:
    st.session_state["selected_query"] = "1. Count asteroid approaches"

# Velocity
if "min_velocity" not in st.session_state:
    st.session_state["min_velocity"] = 0.0
if "max_velocity" not in st.session_state:
    st.session_state["max_velocity"] = 100000.0

# Diameter
if "min_diameter" not in st.session_state:
    st.session_state["min_diameter"] = 0.0
if "max_diameter" not in st.session_state:
    st.session_state["max_diameter"] = 5.0

# Astronomical Units
if "min_au" not in st.session_state:
    st.session_state["min_au"] = 0.0
if "max_au" not in st.session_state:
    st.session_state["max_au"] = 0.05

# Lunar Distance
if "min_ld" not in st.session_state:
    st.session_state["min_ld"] = 0.0
if "max_ld" not in st.session_state:
    st.session_state["max_ld"] = 10.0

# Hazardous filter
if "hazardous" not in st.session_state:
    st.session_state["hazardous"] = "Both"


# ----------------------------
# 3. Header
# ----------------------------
st.markdown("""
<div class="main-header">
    <h1>🌌 NASA NEO Tracking & Insights Dashboard</h1>
    <h3>🛰️ Advanced Space Object Monitoring & Analysis</h3>
    <p>Explore 2024 asteroid data, approach speeds, distances, and hazard insights using SQL-powered queries</p>
</div>
""", unsafe_allow_html=True)

# ----------------------------
# 4. DB helpers
# ----------------------------
def get_connection():
    """
    Create and return a new MySQL/TiDB connection using Streamlit secrets.
    """
    return mysql.connector.connect(
        host=st.secrets["host"],
        user=st.secrets["user"],
        password=st.secrets["password"],
        database=st.secrets["name"],
        port=st.secrets.get("port", 4000),  # default port; override in st.secrets if needed
    )

def run_query(sql, params=None):
    """
    Run a SELECT query and return a pandas DataFrame.
    The connection is opened and closed inside this function.
    """
    conn = None
    try:
        conn = get_connection()
        df = pd.read_sql(sql, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Database query failed: {e}")
        return pd.DataFrame()
    finally:
        if conn is not None:
            conn.close()

# ----------------------------
# 5. Top metrics (overview)
# ----------------------------
try:
    total_asteroids_df = run_query(
        "SELECT COUNT(DISTINCT id) AS count FROM asteroids"
    )
    total_approaches_df = run_query(
        "SELECT COUNT(*) AS count FROM close_approach"
    )
    hazardous_count_df = run_query(
        "SELECT COUNT(*) AS count FROM asteroids WHERE is_potentially_hazardous_asteroid = 1"
    )

    total_asteroids = int(total_asteroids_df.iloc[0]["count"]) if not total_asteroids_df.empty else 0
    total_approaches = int(total_approaches_df.iloc[0]["count"]) if not total_approaches_df.empty else 0
    hazardous_count = int(hazardous_count_df.iloc[0]["count"]) if not hazardous_count_df.empty else 0

except Exception as e:
    st.error(f"⚠️ Database connection failed: {e}")
    st.info("🔧 Please check your MySQL connection settings in st.secrets.")
    total_asteroids = total_approaches = hazardous_count = 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-container">
        <h2>🌑 {total_asteroids:,}</h2>
        <p>Total Asteroids Tracked</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-container">
        <h2>🚀 {total_approaches:,}</h2>
        <p>Close Approaches Recorded</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-container">
        <h2>⚠️ {hazardous_count:,}</h2>
        <p>Potentially Hazardous</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    hazard_percentage = (hazardous_count / total_asteroids * 100) if total_asteroids > 0 else 0
    st.markdown(f"""
    <div class="metric-container">
        <h2>📊 {hazard_percentage:.1f}%</h2>
        <p>Hazard Rate</p>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------
# 6. Helper to run + show queries
# ----------------------------
def show_query(sql, show_chart=True):
    """
    Run the given SQL string, show results as a table,
    and optionally show a chart based on the data.
    """
    try:
        df = run_query(sql)

        if df.empty:
            st.warning("No data returned for this query.")
            return df

        st.dataframe(df, use_container_width=True, height=400)

        if show_chart and len(df) > 0:
            if len(df.columns) == 2 and df.columns[1] in ['count', 'approach_count', 'total']:
                fig = px.bar(
                    df.head(10),
                    x=df.columns[0],
                    y=df.columns[1],
                    title=f"Top 10 - {df.columns[1].replace('_', ' ').title()}"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

            elif len(df.columns) > 1 and 'velocity' in df.columns[1].lower():
                fig = px.histogram(
                    df,
                    x=df.columns[1],
                    title=f"Distribution of {df.columns[1].replace('_', ' ').title()}"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

        return df

    except Exception as e:
        st.error(f"❌ Query execution failed: {e}")
        return pd.DataFrame()

# ----------------------------
# 7. Query definitions
# ----------------------------
queries = {
    "1. Count asteroid approaches": '''
        SELECT neo_reference_id, COUNT(*) AS approach_count
        FROM close_approach
        GROUP BY neo_reference_id
        ORDER BY approach_count DESC
    ''',

    "2. Average velocity per asteroid": '''
        SELECT neo_reference_id, AVG(relative_velocity_km_per_hour) AS avg_velocity
        FROM close_approach
        GROUP BY neo_reference_id
        ORDER BY avg_velocity DESC
    ''',

    "3. Top 10 fastest asteroids": '''
        SELECT neo_reference_id, MAX(relative_velocity_km_per_hour) AS max_velocity
        FROM close_approach
        GROUP BY neo_reference_id
        ORDER BY max_velocity DESC
        LIMIT 10
    ''',

    "4. Hazardous asteroids > 3 approaches": '''
        SELECT ca.neo_reference_id, COUNT(*) AS approach_count
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        WHERE a.is_potentially_hazardous_asteroid = 1
        GROUP BY ca.neo_reference_id
        HAVING COUNT(*) > 3
    ''',

    #MySQL-friendly month extraction
    "5. Month with most approaches": '''
        SELECT DATE_FORMAT(close_approach_date, '%Y-%m') AS month, COUNT(*) AS count
        FROM close_approach
        GROUP BY month
        ORDER BY count DESC
        LIMIT 1
    ''',

    "6. Fastest ever approach": '''
        SELECT neo_reference_id, MAX(relative_velocity_km_per_hour) AS fastest_speed
        FROM close_approach
        GROUP BY neo_reference_id
        ORDER BY fastest_speed DESC
        LIMIT 1
    ''',

    "7. Sort by max estimated diameter": '''
        SELECT id, name, estimated_diameter_max_km
        FROM asteroids
        ORDER BY estimated_diameter_max_km DESC
    ''',

    "8. Closest approach getting nearer over time": '''
        SELECT *
        FROM close_approach
        ORDER BY neo_reference_id, close_approach_date
    ''',

    "9. Closest approach date & distance": '''
        SELECT a.name,
               ca.close_approach_date,
               MIN(ca.miss_distance_km) AS closest_approach
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        GROUP BY a.id, a.name, ca.close_approach_date
        ORDER BY closest_approach ASC
    ''',

    "10. Velocity > 50,000 km/h": '''
        SELECT DISTINCT a.name, ca.relative_velocity_km_per_hour
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        WHERE ca.relative_velocity_km_per_hour > 50000
    ''',

    "11. Approaches per month": '''
        SELECT DATE_FORMAT(close_approach_date, '%Y-%m') AS month, COUNT(*) AS total
        FROM close_approach
        GROUP BY month
        ORDER BY total DESC
    ''',

    "12. Brightest asteroid (lowest magnitude)": '''
        SELECT id, name, absolute_magnitude_h
        FROM asteroids
        ORDER BY absolute_magnitude_h ASC
        LIMIT 1
    ''',

    "13. Hazardous vs Non-hazardous count": '''
        SELECT is_potentially_hazardous_asteroid, COUNT(*) AS count
        FROM asteroids
        GROUP BY is_potentially_hazardous_asteroid
    ''',

    "14. Asteroids < 1 LD": '''
        SELECT a.name,
               ca.close_approach_date,
               ca.miss_distance_lunar
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        WHERE ca.miss_distance_lunar < 1
        ORDER BY ca.miss_distance_lunar
    ''',

    "15. Asteroids < 0.05 AU": '''
        SELECT a.name,
               ca.close_approach_date,
               ca.astronomical
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        WHERE ca.astronomical < 0.05
        ORDER BY ca.astronomical
    ''',

    "Bonus 1: Orbiting bodies (non-Earth)": '''
        SELECT orbiting_body, COUNT(*) AS count
        FROM close_approach
        WHERE orbiting_body != 'Earth'
        GROUP BY orbiting_body
        ORDER BY count DESC
    ''',

    "Bonus 2: Avg miss distance by hazard type": '''
        SELECT a.is_potentially_hazardous_asteroid,
               AVG(ca.miss_distance_km) AS avg_miss_distance
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        GROUP BY a.is_potentially_hazardous_asteroid
    ''',

    "Bonus 3: Top 5 closest approaches": '''
        SELECT a.name,
               ca.close_approach_date,
               ca.miss_distance_km
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        ORDER BY ca.miss_distance_km ASC
        LIMIT 5
    ''',

    "Bonus 4: Count of hazardous asteroids": '''
        SELECT COUNT(DISTINCT id) AS hazardous_asteroid_count
        FROM asteroids
        WHERE is_potentially_hazardous_asteroid = 1
    ''',

    "Bonus 5: Frequent <1 LD asteroids": '''
        SELECT ca.neo_reference_id,
               a.name,
               COUNT(*) AS close_pass_count
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        WHERE ca.miss_distance_lunar < 1
        GROUP BY ca.neo_reference_id, a.name
        HAVING COUNT(*) > 1
        ORDER BY close_pass_count DESC
    '''
}

# ----------------------------
# 8. Sidebar – query selection
# ----------------------------
st.sidebar.markdown("## 🎯 Query Selection")
st.sidebar.markdown("Choose from our comprehensive set of asteroid analysis queries:")

query_categories = {
    "📈 Statistical Analysis": [
        "1. Count asteroid approaches",
        "2. Average velocity per asteroid",
        "3. Top 10 fastest asteroids",
        "11. Approaches per month"
    ],
    "⚠️ Hazard Assessment": [
        "4. Hazardous asteroids > 3 approaches",
        "13. Hazardous vs Non-hazardous count",
        "Bonus 4: Count of hazardous asteroids",
        "Bonus 2: Avg miss distance by hazard type"
    ],
    "🏃‍♂️ Speed & Motion": [
        "6. Fastest ever approach",
        "10. Velocity > 50,000 km/h"
    ],
    "📏 Distance & Size": [
        "7. Sort by max estimated diameter",
        "9. Closest approach date & distance",
        "14. Asteroids < 1 LD",
        "15. Asteroids < 0.05 AU",
        "Bonus 3: Top 5 closest approaches"
    ],
    "📅 Temporal Analysis": [
        "5. Month with most approaches",
        "8. Closest approach getting nearer over time"
    ],
    "🌟 Special Queries": [
        "12. Brightest asteroid (lowest magnitude)",
        "Bonus 1: Orbiting bodies (non-Earth)",
        "Bonus 5: Frequent <1 LD asteroids"
    ]
}

# When a button is clicked, set selected_query AND adjust sliders
for category, queries_list in query_categories.items():
    with st.sidebar.expander(category):
        for query_label in queries_list:
            if st.button(query_label, key=f"btn_{query_label}"):
                st.session_state["selected_query"] = query_label

                # OPTIONAL: set slider defaults depending on query
                if query_label == "10. Velocity > 50,000 km/h":
                    st.session_state["min_velocity"] = 50000.0
                    st.session_state["max_velocity"] = 100000.0
                elif query_label == "14. Asteroids < 1 LD":
                    st.session_state["min_ld"] = 0.0
                    st.session_state["max_ld"] = 1.0
                elif query_label == "15. Asteroids < 0.05 AU":
                    st.session_state["min_au"] = 0.0
                    st.session_state["max_au"] = 0.05
                # you can add more special cases if you want

# Use the stored selection
selected_query = st.session_state["selected_query"]

# ----------------------------
# 9. Show selected query
# ----------------------------
st.markdown(f"""
<div class="query-section">
    <h2>🔍 {selected_query}</h2>
</div>
""", unsafe_allow_html=True)

show_query(queries[selected_query])

# ----------------------------
# 10. Advanced Filters
# ----------------------------
st.markdown("""
<div class="filter-section">
    <h2>🎛️ Advanced Asteroid Approach Filters</h2>
    <p>Customize your search parameters to find specific asteroid approaches</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("📅 Date & Time Filters")
    selected_date = st.date_input(
        "Select Close Approach Date (after)",
        datetime(2024, 1, 1)
    )
    st.info("📊 Data Range: January 1, 2024 - December 31, 2024")

    st.subheader("🚀 Velocity Filters")
    min_velocity = st.slider(
        "Minimum Relative Velocity (km/h)",
        0.0, 100000.0,
        key="min_velocity"
    )
    max_velocity = st.slider(
        "Maximum Relative Velocity (km/h)",
        0.0, 100000.0,
        key="max_velocity"
    )

    st.subheader("📏 Size Filters")
    min_diameter = st.slider(
        "Minimum Estimated Diameter (km)",
        0.0, 50.0,
        key="min_diameter"
    )
    max_diameter = st.slider(
        "Maximum Estimated Diameter (km)",
        0.0, 50.0,
        key="max_diameter"
    )

with col2:
    st.subheader("🌍 Distance Filters (Astronomical Units)")
    min_au = st.slider(
        "Minimum AU",
        0.0, 1.0,
        key="min_au"
    )
    max_au = st.slider(
        "Maximum AU",
        0.0, 1.0,
        key="max_au"
    )

    st.subheader("🌙 Distance Filters (Lunar Distance)")
    min_ld = st.slider(
        "Minimum LD",
        0.0, 100.0,
        key="min_ld"
    )
    max_ld = st.slider(
        "Maximum LD",
        0.0, 100.0,
        key="max_ld"
    )

    st.subheader("⚠️ Hazard Classification")
    hazardous = st.selectbox(
        "Potentially Hazardous?",
        ["Both", "Yes", "No"],
        key="hazardous"
    )


# ----------------------------
# 11. Colab launch instructions
# ----------------------------
st.markdown("""
---
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 10px; color: white;">
    <h2>🚀 Launch Instructions for Google Colab</h2>
    <p>Follow these steps to run this dashboard in Google Colab:</p>
</div>
""", unsafe_allow_html=True)

st.code("""
# Step 1: Get your external IP (this will be your password)
!wget -q -O - ipv4.icanhazip.com

# Step 2: Install required packages (if not already installed)
!pip install streamlit plotly mysql-connector-python

# Step 3: Launch the app
!streamlit run "Nasa_Neo script.py" & npx localtunnel --port 8501
""", language="bash")

st.markdown("""
**📋 Then follow these steps:**
1. ✅ Enter `y` when prompted to proceed  
2. 🔗 Copy the generated link (e.g., `https://fruity-aliens-unite.loca.lt/`)  
3. 🌐 Paste it in your browser  
4. 🔑 Enter the IP address from Step 1 as the password  
5. 🎉 You'll be redirected to your enhanced Streamlit app!

**💡 Pro Tips:**
- Ensure your database is reachable from Colab and credentials are in `st.secrets`  
- The dashboard works best with a stable internet connection  
- Use the interactive filters to explore different aspects of asteroid data  
""")
