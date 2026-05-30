import streamlit as st
import altair as alt
import pandas as pd

# Import functions from your modules
from queries.q1_q5 import create_character_plot, load_data_q1_q5
# from queries.q2 import create_timeline_plot, load_data_q2
# from queries.q3_q4 import create_diverging_difference_plot, create_episode_comparison_plot, load_data_q3_q4
from queries.q3_q4_v2 import  build_dashboard_html, load_data, build_dashboard

# Enable VegaFusion globally for the app
alt.data_transformers.disable_max_rows()


# Set up the main page configuration once
st.set_page_config(layout="wide", page_title="The Simpsons Dialogue Dashboard")

st.title("The Simpsons: Comprehensive Dialogue Analysis")

# # ==========================================
# # ROW 1: Q1 & Q5 (Distribution)
# # ==========================================
st.header("1. Character Dialogue Distribution")
st.markdown("Click on a character's bar on the left to **filter** their specific dialogue distribution on the right. Shift-click to select multiple characters.")


data_q1_q5, data_q1_q5_agg, all_faces = load_data_q1_q5()

# # --- NEW: Streamlit Multiselect for 5 Characters Max ---
all_characters = sorted(data_q1_q5_agg['character'].unique().tolist())
default_5_chars = ["Apu", "Bart", "Homer", "Lisa", "Marge"]

selected_chars = st.multiselect(
    "Select Characters (Max 5):",
    options=all_characters,
    default=default_5_chars,
    max_selections=5 # <--- This natively enforces the maximum 5 rule!
)

# # Stop the app from rendering an empty chart if the user clears all characters
if not selected_chars:
    st.info("Please select at least one character to view the chart.")
else:
    # Filter the dataframes to ONLY contain the selected characters
    filtered_agg = data_q1_q5_agg[data_q1_q5_agg['character'].isin(selected_chars)]
    filtered_dist = data_q1_q5[data_q1_q5['character'].isin(selected_chars)]

    # Generate the chart using the filtered data
    chart = create_character_plot(df_all_faces=all_faces, df_agg=filtered_agg, df_dist=filtered_dist) 

    # Render in Streamlit
    st.altair_chart(chart, use_container_width=True)

#st.divider()

# # ==========================================
# # ROW 2: Q2 (Timeline)
# # ==========================================
# #st.header("2. Dialogue Timeline Analysis")
# #st.markdown("Select characters from the dropdown below to track their word counts over the seasons. Hover over the points to see specific values and character images.")

# df_q2_full = load_data_q2()

# all_characters_q2 = sorted(df_q2_full['character'].unique().tolist())
# default_chars_q2 = ['Homer', 'Marge', 'Bart']

# selected_chars_q2 = st.multiselect(
#     "Select Characters to Display:", 
#     options=all_characters_q2, 
#     default=default_chars_q2,
#     key="timeline_multiselect" 
# )

# if not selected_chars_q2:
#     st.info("Please select at least one character from the dropdown menu above.")
# else:
#     data_filtered_q2 = df_q2_full[df_q2_full['character'].isin(selected_chars_q2)]
#     chart_q2 = create_timeline_plot(data_filtered_q2)
#     st.altair_chart(chart_q2, use_container_width=True)

# #st.divider()

# # ==========================================
# # ROW 3: Q3 and Q4 (Comparison)
# # ==========================================
# #st.header("3. Episode Comparison Analysis")
# #st.markdown("Compare character word counts episode-by-episode. Select exactly 2 characters to see the difference plot.")

# df_q3_full = load_data_q3_q4()

# col1, col2 = st.columns(2)

# with col1:
#     all_characters_q3 = sorted(df_q3_full['character'].unique().tolist())
#     selected_chars_q3 = st.multiselect(
#         "Select Characters:", 
#         options=all_characters_q3, 
#         default=['Bart', 'Lisa'],
#         key="comparison_multiselect"
#     )

# with col2:
#     available_seasons = sorted(df_q3_full['season'].dropna().unique().tolist())
#     selected_season = st.selectbox(
#         "Select Season:",
#         options=available_seasons,
#         index=0 
#     )

# if not selected_chars_q3:
#     st.info("Please select at least one character to view the chart.")
# else:
#     mask = (df_q3_full['character'].isin(selected_chars_q3)) & (df_q3_full['season'] == selected_season)
#     data_filtered_q3 = df_q3_full[mask]
    
#     if data_filtered_q3.empty:
#         st.warning(f"No data available for the selected characters in Season {selected_season}.")
#     else:
#         chart_col1, chart_col2 = st.columns(2)
        
#         with chart_col1:
#             comparison_chart = create_episode_comparison_plot(data_filtered_q3, selected_season, selected_chars_q3)
#             st.altair_chart(comparison_chart, use_container_width=True)
            
#         with chart_col2:
#             difference_chart = create_diverging_difference_plot(data_filtered_q3, selected_season, selected_chars_q3)
#             st.altair_chart(difference_chart, use_container_width=True)

    


## Optionn 2

"""
app.py
------
Streamlit dashboard for the Simpsons Word-Count explorer.

Run with:
    streamlit run app.py

The chart is rendered via st.components.v1.html() using a self-contained
Vega-Lite HTML export.  This avoids the constant remount/blink that affects
st.altair_chart(), because the iframe is never touched by Streamlit after the
initial paint — all selections and interactions live purely in JavaScript.
"""

import streamlit as st
import streamlit.components.v1 as components


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Simpsons Word Count",
    page_icon="🍩",
    layout="wide",
)

st.title("🍩 Simpsons Word Count Dashboard")
st.caption(
    "Select two characters and a season to compare word counts across episodes. "
    "Click an episode bar to see the cumulative word count within that episode."
)

# ---------------------------------------------------------------------------
# Data (cached – loaded once, never re-read on re-runs)
# ---------------------------------------------------------------------------

@st.cache_data
def get_data():
    return load_data("../data/data_Q3.csv", "../data/data_Q4.csv")

data_q3, data_q4 = get_data()

# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------

view = st.radio(
    "Chart view",
    options=["absolute", "relative"],
    format_func=lambda v: "Absolute word count" if v == "absolute" else "Relative advantage",
    horizontal=True,
)

# ---------------------------------------------------------------------------
# Chart HTML (cached per view – rebuilt only when view toggle changes)
# ---------------------------------------------------------------------------

@st.cache_data
def get_chart_html(view: str) -> str:
    return build_dashboard_html(data_q3, data_q4, view=view)

html = get_chart_html(view)

# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

# height should comfortably contain the 600px-tall charts plus Vega padding.
# scrolling=True lets the user pan horizontally on narrow screens.
components.html(html, height=700, scrolling=True)