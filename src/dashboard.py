import streamlit as st
import altair as alt
import pandas as pd
import streamlit.components.v1 as components
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
components.html(html, height=550, scrolling=False)

st.header("2. Character Word By Episode Comparison")

view = st.radio(
    "View by:",
    options=["absolute", "relative"],
    format_func=lambda v: "Absolute word count" if v == "absolute" else "Relative advantage",
    horizontal=True,
)

html = create_plot_q4_html(view=view) 
components.html(html, height=1000, scrolling=False)



