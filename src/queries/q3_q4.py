import streamlit as st
import pandas as pd
import altair as alt

# Enable VegaFusion for larger datasets
alt.data_transformers.enable("vegafusion")

def create_episode_comparison_plot(df: pd.DataFrame, season: int, characters: list):
    """
    Generates a dumbbell-style plot comparing word counts between characters 
    for each episode in a specific season.
    """
    # Create a dynamic title based on the selected characters and season
    if len(characters) == 2:
        char_title = f"{characters[0]} vs {characters[1]}"
    elif len(characters) == 1:
        char_title = f"{characters[0]}'s"
    else:
        char_title = "Selected Characters"
        
    chart_title = f"{char_title} Word Count by Episode (Season {season})"

    # 1. Base chart encoding
    # Using detail="number_in_season:O" ensures the line only connects points within the same episode
    chart = alt.Chart(df).encode(
        x=alt.X("word_count:Q", title="Word Count"),
        y=alt.Y("number_in_season:O", title="Episode Number in Season"),
        detail="number_in_season:O", 
        tooltip=[
            alt.Tooltip("season:O", title="Season"), 
            alt.Tooltip("number_in_season:O", title="Episode"), 
            alt.Tooltip("character:N", title="Character"), 
            alt.Tooltip("word_count:Q", title="Word Count")
        ]
    )

    # 2. Add the connecting line
    line = chart.mark_line(color="#db646f", strokeWidth=4)

    # 3. Add the character images at the points
    faces = chart.mark_image(width=20, height=20).encode(
        url="image:N"
    )

    # 4. Layer them together and configure properties
    final_chart = (line + faces).properties(
        title=chart_title,
        height=500
    )
    
    return final_chart

# ==========================================
# STREAMLIT APP DASHBOARD
# ==========================================

st.set_page_config(layout="wide", page_title="The Simpsons Episode Comparison")

st.title("The Simpsons: Episode Comparison Analysis")
st.markdown("Compare character word counts episode-by-episode. Select your characters and the season below.")

# 1. Data Loading
@st.cache_data
def load_data_q3_q4():
    # Loading Q3 (Q4 is loaded but unused in your original snippet, so I've omitted it here 
    # to save memory. Add it back if you need it for other charts!)
    df_q3 = pd.read_csv('../data/data_Q3.csv')
    return df_q3

df_full = load_data_q3_q4()

# 2. Layout for Filters
col1, col2 = st.columns(2)

with col1:
    # Character Multiselect
    all_characters = sorted(df_full['character'].unique().tolist())
    selected_chars = st.multiselect(
        "Select Characters:", 
        options=all_characters, 
        default=['Bart', 'Lisa']
    )

with col2:
    # Season Selectbox (Replacing Altair's binding_select)
    available_seasons = sorted(df_full['season'].dropna().unique().tolist())
    selected_season = st.selectbox(
        "Select Season:",
        options=available_seasons,
        index=0 # Defaults to the first available season
    )


# 3. Filter Data & Render Plot
if not selected_chars:
    st.info("Please select at least one character to view the chart.")
else:
    # Apply Streamlit filters to the DataFrame
    mask = (df_full['character'].isin(selected_chars)) & (df_full['season'] == selected_season)
    data_filtered = df_full[mask]
    
    if data_filtered.empty:
        st.warning(f"No data available for the selected characters in Season {selected_season}.")
    else:
        # Generate and display the chart
        comparison_chart = create_episode_comparison_plot(data_filtered, selected_season, selected_chars)
        st.altair_chart(comparison_chart, use_container_width=True)