import streamlit as st
import altair as alt
import pandas as pd
from queries.q1_q5 import create_plot_q1_q5_html
from queries.q3_q4 import create_plot_q4_html

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

alt.data_transformers.disable_max_rows()


st.set_page_config(layout="wide", page_title="The Simpsons Dialogue Dashboard")



st.header("1. Character Dialogue Distribution")



html = create_plot_q1_q5_html()
st.iframe(html)

st.header("2. Character Word By Episode Comparison")

view = st.radio(
    "View by:",
    options=["absolute", "relative"],
    format_func=lambda v: "Absolute word count" if v == "absolute" else "Relative advantage",
    horizontal=True,
)

html = create_plot_q4_html(view=view) 
st.iframe(html)



