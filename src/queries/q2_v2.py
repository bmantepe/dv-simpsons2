import streamlit as st
import pandas as pd
import altair as alt

# Enable VegaFusion for larger datasets

def create_q2_plot(df: pd.DataFrame):

    nearest = alt.selection_point(nearest=True, on='mouseover', fields=['season'], empty=False)
    legend_selection = alt.selection_point(fields=['character'], bind='legend')

    # 2. Invisible selectors for the hover effect
    selectors = alt.Chart(df).mark_point().encode(
        x='season:O',
        opacity=alt.value(0),
    ).add_params(nearest)  

    lines_main = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X('season:O', title='Season'),
        y=alt.Y('word_count:Q', title='Total Word Count'),
        color=alt.Color('character:N', legend=alt.Legend(title="Character")),
        opacity=alt.when(legend_selection).then(alt.value(1)).otherwise(alt.value(0.2))
    ).add_params(nearest, legend_selection)

    text = lines_main.mark_text(align='left', dx=10, dy=-15).encode(
        text=alt.condition(nearest, 'word_count:N', alt.value(''))
    )

    images_point = alt.Chart(df).mark_image(
        width=30, height=30, align='center', baseline='middle'
    ).encode(
        x='season:O',
        y='word_count:Q',
        url='image:N'
    ).transform_filter(
        nearest
    )

    rules = alt.Chart(df).mark_rule(color='gray').encode(
        x='season:O',
    ).transform_filter(
        nearest
    )

    chart = alt.layer(
        selectors, lines_main, text, rules, images_point
    ).properties(
        height=400,
        title='Total Word Count per Season for Selected Characters'
    ).configure_axisX(
        labelAngle=0
    )

    return chart


@st.cache_data
def load_data_q2():
    # Load ALL count types — filtering happens inside Vega-Lite via view_selector
    data = pd.read_csv('../data/data_Q2.csv')
    return data


@st.cache_resource
def create_plot_q2_html():
    data_q2 = load_data_q2()
    chart = create_q2_plot(data_q2)
    return chart.to_html()


