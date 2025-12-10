import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Streamlit UI setup with enhanced styling
st.set_page_config(
    page_title="NASA NEO Tracker",
    page_icon="🚀",
    layout='wide',
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced visual appeal
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

# Enhanced title and intro with visual elements
st.markdown("""
<div class="main-header">
    <h1>🌌 NASA NEO Tracking & Insights Dashboard</h1>
    <h3>🛰️ Advanced Space Object Monitoring & Analysis</h3>
    <p>Explore 2024 asteroid data, approach speeds, distances, and hazard insights using SQL-powered queries</p>
</div>
""", unsafe_allow_html=True)

# Connect to the database
def get_connection():
    """
    Create and return a new MySQL connection using Streamlit secrets.
    This function is called every time we run a query.
    """
    return mysql.connector.connect(
        host=st.secrets["host"],
        user=st.secrets["user"],
        password=st.secrets["password"],
        database=st.secrets["name"],
        port=st.secrets.get("port", 4000),  # 3306 is MySQL default tidb port 4000
    )

def run_query(sql, params=None):
    """
    Run a SELECT query and return a pandas DataFrame.
    The connection is opened and closed inside this function.
    """
    conn = None
    try:
        conn = get_connection()
        # pandas will handle cursor and fetching
        df = pd.read_sql(sql, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Database query failed: {e}")
        return pd.DataFrame()
    finally:
        if conn is not None:
            conn.close()
    
    # Get database stats for overview
    try:
        total_asteroids_df = run_query("SELECT COUNT(DISTINCT id) AS count FROM asteroids")
        total_approaches_df = run_query("SELECT COUNT(*) AS count FROM close_approach")
        hazardous_count_df = run_query(
            "SELECT COUNT(*) AS count FROM asteroids WHERE is_potentially_hazardous_asteroid = 1"
        )
    
        total_asteroids = int(total_asteroids_df.iloc[0]["count"]) if not total_asteroids_df.empty else 0
        total_approaches = int(total_approaches_df.iloc[0]["count"]) if not total_approaches_df.empty else 0
        hazardous_count = int(hazardous_count_df.iloc[0]["count"]) if not hazardous_count_df.empty else 0
    
        # (Your metric UI code stays the same, just uses the three numbers above)
    except Exception as e:
    st.error(f"⚠️ Database connection failed: {e}")
    st.info("🔧 Please check your MySQL connection settings in st.secrets.")
    
    # Display key metrics at the top
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
    
except Exception as e:
    st.error(f"⚠️ Database connection failed: {e}")
    st.info("🔧 Please ensure 'Asteroid_Data.db' is in the same directory as this script.")

# Helper function to run and display SQL queries with enhanced visualization
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

        # Display dataframe
        st.dataframe(df, use_container_width=True, height=400)

        # Simple auto-charts for some shapes
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
# 4. Using show_query for selected query
# ----------------------------

st.markdown(f"""
<div class="query-section">
    <h2>🔍 {selected_query}</h2>
</div>
""", unsafe_allow_html=True)

# Simply call show_query with the SQL string
show_query(queries[selected_query])

# Enhanced sidebar with better organization
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

# Create expandable sections in sidebar
selected_query = None
for category, queries_list in query_categories.items():
    with st.sidebar.expander(category):
        for query in queries_list:
            if st.button(query, key=f"btn_{query}"):
                selected_query = query

# If no button clicked, default to first query
if selected_query is None:
    selected_query = "1. Count asteroid approaches"

# All Queries defined here (same as original)
queries = {
    "1. Count asteroid approaches": '''
        SELECT neo_reference_id, COUNT(*) AS approach_count
        FROM close_approach
        GROUP BY neo_reference_id
        ORDER BY approach_count DESC
    ''',
    "2. Average velocity per asteroid": '''
        SELECT neo_reference_id, AVG(relative_velocity_kmph) AS avg_velocity
        FROM close_approach
        GROUP BY neo_reference_id
        ORDER BY avg_velocity DESC
    ''',
    "3. Top 10 fastest asteroids": '''
        SELECT neo_reference_id, MAX(relative_velocity_kmph) AS max_velocity
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
    "5. Month with most approaches": '''
        SELECT strftime('%Y-%m', close_approach_date) AS month, COUNT(*) AS count
        FROM close_approach
        GROUP BY month
        ORDER BY count DESC
        LIMIT 1
    ''',
    "6. Fastest ever approach": '''
        SELECT neo_reference_id, MAX(relative_velocity_kmph) AS fastest_speed
        FROM close_approach
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
        SELECT a.name, ca.close_approach_date, MIN(ca.miss_distance_km) AS closest_approach
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        GROUP BY a.id
        ORDER BY closest_approach ASC
    ''',
    "10. Velocity > 50,000 km/h": '''
        SELECT DISTINCT a.name, ca.relative_velocity_kmph
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        WHERE ca.relative_velocity_kmph > 50000
    ''',
    "11. Approaches per month": '''
        SELECT strftime('%Y-%m', close_approach_date) AS month, COUNT(*) AS total
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
        SELECT a.name, ca.close_approach_date, ca.miss_distance_lunar
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        WHERE ca.miss_distance_lunar < 1
        ORDER BY ca.miss_distance_lunar
    ''',
    "15. Asteroids < 0.05 AU": '''
        SELECT a.name, ca.close_approach_date, ca.astronomical
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
        SELECT a.is_potentially_hazardous_asteroid, AVG(ca.miss_distance_km) AS avg_miss_distance
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        GROUP BY a.is_potentially_hazardous_asteroid
    ''',
    "Bonus 3: Top 5 closest approaches": '''
        SELECT a.name, ca.close_approach_date, ca.miss_distance_km
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
        SELECT ca.neo_reference_id, a.name, COUNT(*) AS close_pass_count
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        WHERE ca.miss_distance_lunar < 1
        GROUP BY ca.neo_reference_id
        HAVING COUNT(*) > 1
        ORDER BY close_pass_count DESC
    '''
}

# Display selected query results
st.markdown(f"""
<div class="query-section">
    <h2>🔍 {selected_query}</h2>
</div>
""", unsafe_allow_html=True)

if 'conn' in locals():
    show_query(queries[selected_query])

# Enhanced Filters Section
st.markdown("""
<div class="filter-section">
    <h2>🎛️ Advanced Asteroid Approach Filters</h2>
    <p>Customize your search parameters to find specific asteroid approaches</p>
</div>
""", unsafe_allow_html=True)

# Organized filter controls in columns
col1, col2 = st.columns(2)

with col1:
    st.subheader("📅 Date & Time Filters")
    selected_date = st.date_input("Select Close Approach Date (after)", datetime(2024, 1, 1))
    st.info("📊 Data Range: January 1, 2024 - December 31, 2024")
    
    st.subheader("🚀 Velocity Filters")
    min_velocity = st.slider("Minimum Relative Velocity (km/h)", 0.0, 100000.0, 0.0, 1000.0)
    max_velocity = st.slider("Maximum Relative Velocity (km/h)", 0.0, 100000.0, 50000.0, 1000.0)
    
    st.subheader("📏 Size Filters")
    min_diameter = st.slider("Minimum Estimated Diameter (km)", 0.0, 50.0, 0.0, 0.1)
    max_diameter = st.slider("Maximum Estimated Diameter (km)", 0.0, 50.0, 5.0, 0.1)

with col2:
    st.subheader("🌍 Distance Filters (Astronomical Units)")
    min_au = st.slider("Minimum AU", 0.0, 1.0, 0.0, 0.01)
    max_au = st.slider("Maximum AU", 0.0, 1.0, 0.05, 0.01)
    
    st.subheader("🌙 Distance Filters (Lunar Distance)")
    min_ld = st.slider("Minimum LD", 0.0, 100.0, 0.0, 1.0)
    max_ld = st.slider("Maximum LD", 0.0, 100.0, 10.0, 1.0)
    
    st.subheader("⚠️ Hazard Classification")
    hazardous = st.selectbox("Potentially Hazardous?", ["Both", "Yes", "No"])

# Filter query (same as original)
# ----------------------------
# 5. Corrected filter query
# ----------------------------

filter_query = f'''
SELECT a.name,
       ca.close_approach_date,
       ca.relative_velocity_kmph,
       ca.miss_distance_km,
       ca.miss_distance_lunar,
       a.estimated_diameter_min_km,
       a.estimated_diameter_max_km,
       a.is_potentially_hazardous_asteroid
FROM close_approach ca
JOIN asteroids a ON ca.neo_reference_id = a.id
WHERE date(ca.close_approach_date) >= date('{selected_date}')
  AND ca.astronomical BETWEEN {min_au} AND {max_au} -- AU filter
  AND ca.miss_distance_lunar BETWEEN {min_ld} AND {max_ld}
  AND ca.relative_velocity_kmph BETWEEN {min_velocity} AND {max_velocity}
  AND a.estimated_diameter_max_km BETWEEN {min_diameter} AND {max_diameter}
'''

if hazardous == "Yes":
    filter_query += " AND a.is_potentially_hazardous_asteroid = 1"
elif hazardous == "No":
    filter_query += " AND a.is_potentially_hazardous_asteroid = 0"

st.markdown("### 🎯 Filtered Results")
filtered_df = show_query(filter_query, show_chart=False)

if not filtered_df.empty:
    st.success(f"✅ Found {len(filtered_df)} asteroids matching your criteria")
    # (rest of your metrics on filtered_df stay same)
else:
    st.warning("🔍 No asteroids found matching your criteria. Try adjusting the filters.")

# Enhanced launch instructions
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
!pip install streamlit plotly

# Step 3: Launch the app
!streamlit run Nasa_Neo script.py & npx localtunnel --port 8501
""", language="bash")

st.markdown("""
**📋 Then follow these steps:**
1. ✅ Enter `y` when prompted to proceed
2. 🔗 Copy the generated link (e.g., `https://fruity-aliens-unite.loca.lt/`)
3. 🌐 Paste it in your browser
4. 🔑 Enter the IP address from Step 1 as the password
5. 🎉 You'll be redirected to your enhanced Streamlit app!

**💡 Pro Tips:**
- Ensure your `Asteroid_Data.db` file is in the same directory
- The dashboard works best with a stable internet connection
- Use the interactive filters to explore different aspects of asteroid data
""")

# Close database connection
if 'conn' in locals():
    conn.close()
