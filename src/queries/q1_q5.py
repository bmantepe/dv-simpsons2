import streamlit as st
import pandas as pd
import altair as alt

alt.data_transformers.disable_max_rows()


def create_q1_q5_plot(data_q1_q5, data_q1_q5_agg, data_q2):

    char_lookup = data_q1_q5_agg.sort_values('count', ascending=False)[['character', 'image']].drop_duplicates()

    y_enc = alt.Y(
        "character:N",
        sort=data_q1_q5_agg.sort_values('count', ascending=False)['character'].tolist(),
        axis=alt.Axis(domain=False, ticks=False, labels=False, title=None),

    )

    view_selector = alt.selection_point(
        fields=['count_type'],
        bind=alt.binding_radio(
            options=['word_count', 'sentence_count'],
            labels=['Word Count', 'Sentence Count'],
            name='View by: '
        ),
        value='word_count',
        name='view_selector',
    )

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
        .mark_image(width=40, height=40, yOffset=20)
        .encode(
            x=x_enc_sel,
            url='image:N',
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
            x=alt.X('count:Q', title='Total Count'),
            y=y_enc,
            tooltip=[
                alt.Tooltip('character:N', title='Character'),
                alt.Tooltip('count:Q', title='Total Count'),
            ],
        )
        .transform_filter(selector)
        .transform_filter(view_selector)
    )

    flags = (
        alt.Chart(data_q1_q5.assign(zero=0))
        .mark_image(width=35, height=35, clip=False, xOffset=-20)
        .encode(
            y=y_enc,
            x=alt.X('zero:Q'),
            url='image:N',
        )
        .transform_filter(selector)
        .transform_filter(view_selector)
    )

    barplot_final = (bars + flags).properties(width=400, title='Total Count per Character')

    # --- Jitter + mean chart ---

    gaussian_jitter = (
        alt.Chart(data_q1_q5, title='Count Distribution')
        .mark_circle(size=8)
        .encode(
            y=y_enc,
            x=alt.X('count:Q', title='Count'),
            yOffset='jitter:Q',
        )
        .transform_calculate(jitter="sqrt(-2*log(random()))*cos(2*PI*random())")
        .transform_filter(selector)
        .transform_filter(view_selector)
    )

    mean_bar = (
        alt.Chart(data_q1_q5)
        .mark_tick(color='red', size=30, thickness=3)
        .transform_filter(selector)
        .transform_filter(view_selector)
        .transform_aggregate(mean_wc='mean(count)', groupby=['character'])
        .encode(
            x=alt.X('mean_wc:Q'),
            y=y_enc,
        )
    )

    jitter_final = (gaussian_jitter + mean_bar).properties(width=400,)

    # --- Line chart (Q2) ---

    nearest = alt.selection_point(nearest=True, on='mouseover', fields=['season'], empty=False)
    legend_selection = alt.selection_point(fields=['character'], bind='legend')

    selectors = (
        alt.Chart(data_q2)
        .mark_point()
        .encode(x='season:O', opacity=alt.value(0))
        .transform_filter(selector)
        .transform_filter(view_selector)
        .add_params(nearest)
    )

    lines_main = (
        alt.Chart(data_q2)
        .mark_line(point=True)
        .encode(
            x=alt.X('season:O', title='Season',axis = alt.Axis(labelAngle=0,ticks=False,labelPadding=10)),
            y=alt.Y('count:Q', title='Total Count'),
            color=alt.Color('character:N', legend=alt.Legend(title='Character', orient='right')),
            opacity=alt.when(legend_selection).then(alt.value(1)).otherwise(alt.value(0.2)),
        )
        .transform_filter(selector)
        .transform_filter(view_selector)
        .add_params(nearest, legend_selection)
    )

    text = lines_main.mark_text(align='left', dx=10, dy=-15).encode(
        text=alt.condition(nearest, 'count:N', alt.value(''))
    )

    images_point = (
        alt.Chart(data_q2)
        .mark_image(width=30, height=30, align='center', baseline='middle')
        .encode(
            x='season:O',
            y='count:Q',
            url='image:N',
        )
        .transform_filter(nearest)
        .transform_filter(selector)
        .transform_filter(view_selector)
    )

    rules = (
        alt.Chart(data_q2)
        .mark_rule(color='gray')
        .encode(x='season:O')
        .transform_filter(nearest)
        .transform_filter(selector)
        .transform_filter(view_selector)
    )

    line_chart = alt.layer(
        selectors, lines_main, text, rules, images_point
    ).properties(
        width=800,
        height=490,
        title='Total Count per Season for Selected Characters'
    )

    # --- Final layout ---

    left_side = alt.vconcat(
        character_selector_ui,
        alt.hconcat(barplot_final, jitter_final).resolve_scale(y='shared')
)

    final_layout = (left_side | line_chart).add_params(
        selector, 
        view_selector
    ).configure_view(
        step=80
    )

    return final_layout


@st.cache_data
def load_raw_data():
    return pd.read_csv('../data/data_Q1_Q5.csv')


@st.cache_data
def load_data_q1_q5():
    data = load_raw_data()
    q1_q5_agg = data.groupby(['character', 'count_type', 'image'], as_index=False)['count'].sum()
    return data, q1_q5_agg


@st.cache_data
def load_data_q2():
    return pd.read_csv('../data/data_Q2.csv')


@st.cache_resource
def create_plot_q1_q5_html():
    data_q1_q5, data_q1_q5_agg = load_data_q1_q5()
    data_q2 = load_data_q2()
    chart = create_q1_q5_plot(data_q1_q5, data_q1_q5_agg, data_q2)
    return chart.to_html()