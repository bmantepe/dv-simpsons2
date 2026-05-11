import streamlit as st
import altair as alt

# Import functions from your modules
from queries.q1_q5 import create_character_plot, load_data_q1_q5
from queries.q2 import create_timeline_plot, load_data_q2
from queries.q3_q4 import create_diverging_difference_plot, create_episode_comparison_plot, load_data_q3_q4

# Enable VegaFusion globally for the app
alt.data_transformers.enable("vegafusion")

# Set up the main page configuration once
st.set_page_config(layout="wide", page_title="The Simpsons Dialogue Dashboard")

st.title("The Simpsons: Comprehensive Dialogue Analysis")

# ==========================================
# ROW 1: Q1 & Q5 (Distribution)
# ==========================================
#st.header("1. Character Dialogue Distribution")
#st.markdown("Click on a character's bar on the left to **filter** their specific dialogue distribution on the right. Shift-click to select multiple characters.")

selected_filter = st.radio(
    "Select Analysis Metric:", 
    ["Word", "Sentence"], 
    horizontal=True,
    key="q1_q5_metric_radio"  # <--- ADD THIS UNIQUE KEY
)

data_q1_1, data_q1_2, data_q5_1, data_q5_2 = load_data_q1_q5()

if selected_filter == "Word":
    chart_q1_q5 = create_character_plot("word", data_q1_1, data_q1_2)
else:
    chart_q1_q5 = create_character_plot("sentence", data_q5_1, data_q5_2)

st.altair_chart(chart_q1_q5, use_container_width=True)

#st.divider()

# ==========================================
# ROW 2: Q2 (Timeline)
# ==========================================
#st.header("2. Dialogue Timeline Analysis")
#st.markdown("Select characters from the dropdown below to track their word counts over the seasons. Hover over the points to see specific values and character images.")

df_q2_full = load_data_q2()

all_characters_q2 = sorted(df_q2_full['character'].unique().tolist())
default_chars_q2 = ['Homer', 'Marge', 'Bart']

selected_chars_q2 = st.multiselect(
    "Select Characters to Display:", 
    options=all_characters_q2, 
    default=default_chars_q2,
    key="timeline_multiselect" 
)

if not selected_chars_q2:
    st.info("Please select at least one character from the dropdown menu above.")
else:
    data_filtered_q2 = df_q2_full[df_q2_full['character'].isin(selected_chars_q2)]
    chart_q2 = create_timeline_plot(data_filtered_q2)
    st.altair_chart(chart_q2, use_container_width=True)

#st.divider()

# ==========================================
# ROW 3: Q3 and Q4 (Comparison)
# ==========================================
#st.header("3. Episode Comparison Analysis")
#st.markdown("Compare character word counts episode-by-episode. Select exactly 2 characters to see the difference plot.")

df_q3_full = load_data_q3_q4()

col1, col2 = st.columns(2)

with col1:
    all_characters_q3 = sorted(df_q3_full['character'].unique().tolist())
    selected_chars_q3 = st.multiselect(
        "Select Characters:", 
        options=all_characters_q3, 
        default=['Bart', 'Lisa'],
        key="comparison_multiselect"
    )

with col2:
    available_seasons = sorted(df_q3_full['season'].dropna().unique().tolist())
    selected_season = st.selectbox(
        "Select Season:",
        options=available_seasons,
        index=0 
    )

if not selected_chars_q3:
    st.info("Please select at least one character to view the chart.")
else:
    mask = (df_q3_full['character'].isin(selected_chars_q3)) & (df_q3_full['season'] == selected_season)
    data_filtered_q3 = df_q3_full[mask]
    
    if data_filtered_q3.empty:
        st.warning(f"No data available for the selected characters in Season {selected_season}.")
    else:
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            comparison_chart = create_episode_comparison_plot(data_filtered_q3, selected_season, selected_chars_q3)
            st.altair_chart(comparison_chart, use_container_width=True)
            
        with chart_col2:
            difference_chart = create_diverging_difference_plot(data_filtered_q3, selected_season, selected_chars_q3)
            st.altair_chart(difference_chart, use_container_width=True)