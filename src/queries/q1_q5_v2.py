import streamlit as st
import pandas as pd
import altair as alt
import numpy as np 
import base64
import os


# Disable max rows for instant interactivity in the browser
alt.data_transformers.disable_max_rows()

def create_q1_q5_plot(data_q1_q5, data_q1_q5_agg):


    # One row per character for the selector UI
    char_lookup = data_q1_q5_agg.sort_values('count', ascending=False)[['character', 'image']]

    y_enc = alt.Y(
        "character:N",
        sort=data_q1_q5_agg.sort_values('count', ascending=False)['character'].tolist(),
        axis=alt.Axis(domain=False, ticks=False, labels=False, title=None),
    )

    # Multi-select, capped at 5 by initialising with exactly 5 defaults.
    # Vega-Lite has no built-in max-selection limit, so we default to top 5
    # and note in the UI that only 5 should be active at once.
    selector = alt.selection_point(
        fields=['character'],
        value=[{'character': c} for c in ['Homer', 'Marge', 'Bart', 'Lisa', 'Mr. Burns']],
    )


    x_enc_sel = alt.X(
        'character:N',
        sort=data_q1_q5_agg.sort_values('count', ascending=False)['character'].tolist(),
        axis=alt.Axis(labels=False, ticks=False, title='Select up to 5 characters', orient='top'),
    )

    sel_rects = (
        alt.Chart(char_lookup)
        .mark_rect()
        .encode(
            x=x_enc_sel,
            opacity=alt.when(selector).then(alt.value(1)).otherwise(alt.value(0)),
        )
        .add_params(selector)
    )

    sel_faces = (
        alt.Chart(char_lookup)
        .mark_image(width=40, height=40,yOffset=20)
        .encode(
            x=x_enc_sel,
            url='image:N'
        )
    )

    character_selector_ui = (sel_rects + sel_faces).properties(
        width=800,
        height=50,
        title='',
    )

    # --- Bar chart ---

    bars = (
        alt.Chart(data_q1_q5_agg)
        .mark_bar()
        .encode(
            x=alt.X('count:Q', title='Total Word Count'),
            y=y_enc,
            tooltip=[
                alt.Tooltip('character:N', title='Character'),
                alt.Tooltip('count:Q', title='Total Word Count'),
            ],
            opacity=alt.when(selector).then(alt.value(1)).otherwise(alt.value(0.05)),
        )
        .transform_filter(selector)
    )

    flags = (
        alt.Chart(data_q1_q5.assign(zero=0))
        .mark_image(width=25, height=25, clip=False, xOffset=-12)
        .encode(
            y=y_enc,
            x=alt.X('zero:Q'),
            url='image:N',
        )
        .transform_filter(selector)
    )

    barplot_final = (bars + flags).properties(width=300, title='Total Word Count per Character')

    # --- Jitter + mean chart ---

    gaussian_jitter = (
        alt.Chart(data_q1_q5, title='Word Count Distribution')
        .mark_circle(size=8)
        .encode(
            y=y_enc,
            x=alt.X('count:Q', title='Word Count'),
            yOffset='jitter:Q',
            opacity=alt.when(selector).then(alt.value(0.8)).otherwise(alt.value(0.05)),
        )
        .transform_calculate(jitter="sqrt(-2*log(random()))*cos(2*PI*random())")
        .transform_filter(selector)
    )

    mean_bar = (
        alt.Chart(data_q1_q5)
        .mark_tick(color='red', size=30, thickness=3)
        .transform_filter(selector)
        .transform_aggregate(mean_wc='mean(count)', groupby=['character'])
        .encode(
            x=alt.X('mean_wc:Q'),
            y=y_enc,
        )
    )

    jitter_final = (gaussian_jitter + mean_bar).properties(width=300)

    # --- Final layout ---

    final_layout = alt.vconcat(
        character_selector_ui,
        alt.hconcat(barplot_final, jitter_final)
        .resolve_scale(y='shared')
    ).configure_view(step=40).add_params(selector)

    return final_layout






@st.cache_data
def load_data_q1_q5(view):
    data = pd.read_csv('../data/data_Q1_Q5.csv')
    data = data[data['count_type'] == view]
    q1_q5_agg = data.groupby(['character', 'count_type', 'image'], as_index=False)['count'].sum()
    return data, q1_q5_agg

def create_plot_q1_q5_html(view):
    data_q1_q5, data_q1_q5_agg = load_data_q1_q5(view)
    chart = create_q1_q5_plot(data_q1_q5, data_q1_q5_agg)
    return chart.to_html()

