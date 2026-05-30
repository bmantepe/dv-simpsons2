import streamlit as st
import altair as alt
import pandas as pd
import streamlit.components.v1 as components

# Import functions from your modules
#from queries.q1_q5 import create_character_plot, load_data_q1_q5
from queries.q1_q5_v2 import create_plot_q1_q5_html
# from queries.q2 import create_timeline_plot, load_data_q2
# from queries.q3_q4 import create_diverging_difference_plot, create_episode_comparison_plot, load_data_q3_q4
from queries.q3_q4 import create_plot_q4_html

# Enable VegaFusion globally for the app
alt.data_transformers.disable_max_rows()


# Set up the main page configuration once
st.set_page_config(layout="wide", page_title="The Simpsons Dialogue Dashboard")

# st.title("The Simpsons: Comprehensive Dialogue Analysis")


st.header("1. Character Dialogue Distribution")
st.markdown("Click on a character's bar on the left to **filter** their specific dialogue distribution on the right. Shift-click to select multiple characters.")

word_or_sentence = st.radio(
    "View by",
    options=["Word", "Sentence"],
    format_func=lambda v: "Word Count" if v == "Word" else "Sentence Count",
    horizontal=True,
)

map = {"Word": "word_count", "Sentence": "sentence_count"}
view = map[word_or_sentence]

html = create_plot_q1_q5_html(view)
components.html(html, height=700, scrolling=True)


st.divider()



st.header("2. Dialogue Timeline Analysis")
st.markdown("Select characters from the dropdown below to track their word counts over the seasons. Hover over the points to see specific values and character images.")


st.divider()




st.header("1. Character Dialogue Distribution My version")

view = st.radio(
    "Chart view",
    options=["absolute", "relative"],
    format_func=lambda v: "Absolute word count" if v == "absolute" else "Relative advantage",
    horizontal=True,
)



html = create_plot_q4_html(view=view) 
components.html(html, height=700, scrolling=True)



