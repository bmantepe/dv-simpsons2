import streamlit as st
import altair as alt
import pandas as pd
import streamlit.components.v1 as components

# Import functions from your modules
#from queries.q1_q5 import create_character_plot, load_data_q1_q5
from queries.q1_q5 import create_plot_q1_q5_html
from queries.q2_v2 import create_plot_q2_html

from queries.q3_q4 import create_plot_q4_html

# Inject custom CSS to force the Altair radio buttons to use Streamlit's default font
st.markdown("""
    <style>
    /* Targets the HTML container that holds Altair's radio bindings */
    .vega-bindings {
        font-family: "Source Sans Pro", sans-serif;
        font-size: 14px;
        color: #31333F;
    }
    </style>
""", unsafe_allow_html=True)

# Enable VegaFusion globally for the app
alt.data_transformers.disable_max_rows()


# Set up the main page configuration once
st.set_page_config(layout="wide", page_title="The Simpsons Dialogue Dashboard")

# st.title("The Simpsons: Comprehensive Dialogue Analysis")


st.header("1. Character Dialogue Distribution")
st.markdown("Click on a character's bar on the left to **filter** their specific dialogue distribution on the right. Shift-click to select multiple characters.")



html = create_plot_q1_q5_html()
components.html(html, height=550, scrolling=False)

# Second combined plots
st.header("2. Character Word By Episode Distribution")

view = st.radio(
    "Select the view type:",
    options=["absolute", "relative"],
    format_func=lambda v: "Absolute word count" if v == "absolute" else "Relative advantage",
    horizontal=True,
)

html = create_plot_q4_html(view=view) 
components.html(html, height=700, scrolling=True)



