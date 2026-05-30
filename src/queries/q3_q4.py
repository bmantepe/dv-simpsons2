import altair as alt
import streamlit as st
import pandas as pd


def create_episode_comparison_plot(data_q3, data_q4, type):

    season_df = pd.DataFrame({
        'season': data_q3['season'].unique(),
        'value': [1] * len(data_q3['season'].unique())
    })

    # --- Selectors ---

    season_selector = alt.selection_point(fields=['season'], value=1, name='season_selector')
    char1_selector = alt.selection_point(fields=['character'], name='char1_selector', value='Bart')
    char2_selector = alt.selection_point(fields=['character'], name='char2_selector', value='Lisa')
    episode_selector = alt.selection_point(fields=['episode_id'], on='mouseover', name='episode_selector')

    # --- Season heatmap ---

    heatmap_seasons = alt.Chart(season_df).mark_rect().encode(
        y=alt.Y('season:O', title='Season'),
        color=alt.Color('value:Q', legend=None),
        opacity=alt.when(season_selector).then(alt.value(1)).otherwise(alt.value(0.4)),
    ).add_params(season_selector)

    # --- Character selector UI ---
    # add_params is called on BOTH the heatmap and faces layers for each
    # character — same pattern as the working reference script.

    

    char1_base = alt.Chart(data_q3)

    heatmap1 = char1_base.mark_rect(color='#0e33eb').encode(
        y=alt.Y('character:N', title='Select Character 1'),
        opacity=alt.condition(char1_selector, alt.value(1), alt.value(0))
    ).add_params(char1_selector)

    faces1 = char1_base.mark_image(size=400).encode(
        y=alt.Y('character:N',axis=alt.Axis(labels=False, ticks=False, title=None)),
        url='image:N'
    ).add_params(char1_selector)

    char2_base = alt.Chart(data_q3)

    heatmap2 = char2_base.mark_rect(color='#f40c0c').encode(
        y=alt.Y('character:N', title='Select Character 2'),
        opacity=alt.condition(char2_selector, alt.value(1), alt.value(0))
    ).add_params(char2_selector)

    faces2 = char2_base.mark_image(size=400).encode(
        y=alt.Y('character:N',
                axis=alt.Axis(labels=False, ticks=False, title=None)),
        url='image:N'
    ).add_params(char2_selector)

    selection_ui = alt.hconcat(
        (heatmap1 + faces1),
        (heatmap2 + faces2)
    ).resolve_scale(y='shared')

    # --- Q3: absolute or relative ---

    if type == 'absolute':

        chart = (
            alt.Chart(data_q3)
            .transform_filter(char1_selector | char2_selector)
            .transform_joinaggregate(
                max_row='argmax(word_count)',
                groupby=['season', 'number_in_season']
            )
            .transform_calculate(more_words='datum.max_row.character')
            .encode(
                x=alt.X('word_count:Q', title='Word Count'),
                y=alt.Y('number_in_season:O', title='Episode Number in Season'),
                detail='number_in_season:O',
                tooltip=['season:O', 'number_in_season:O', 'character:N', 'word_count:Q'],
                color=alt.Color('more_words:N', title='More Words', legend=None,
                                scale=alt.Scale(range=['#0e33eb', '#f40c0c'])),
                opacity=alt.condition(episode_selector, alt.value(1), alt.value(0.2))
            )
            .transform_filter(season_selector)
        )

        line = chart.mark_line(strokeWidth=4)
        faces = chart.mark_image(width=20, height=20).encode(url='image:N')
        points = chart.mark_point(size=500, filled=True).encode(
            color=alt.Color('character:N', title='Character')
        )

        q3 = (line + points + faces).properties(
            title='Character Word Count by Episode',
            width=400,
            height=600
        ).add_params(episode_selector, season_selector, char1_selector, char2_selector)

    else:

        base_rel = (
            alt.Chart(data_q3)
            .transform_filter(season_selector & (char1_selector | char2_selector))
            .transform_calculate(
                c1_val=f'datum.character == {char1_selector.name}.character ? datum.word_count : 0',
                c2_val=f'datum.character == {char2_selector.name}.character ? datum.word_count : 0'
            )
            .transform_joinaggregate(
                sum_c1='sum(c1_val)',
                sum_c2='sum(c2_val)',
                groupby=['episode_id']
            )
            .transform_calculate(
                diff='datum.sum_c2 - datum.sum_c1',
                abs_diff='abs(datum.diff)',
                dominant_char=f'datum.diff > 0 ? {char2_selector.name}.character : {char1_selector.name}.character'
            )
        )

        symmetry_fix = (
            base_rel.transform_aggregate(max_abs='max(abs_diff)')
            .transform_calculate(neg_limit='-datum.max_abs', pos_limit='datum.max_abs')
            .mark_rule(opacity=0, tooltip=None)
            .encode(x=alt.X('neg_limit:Q'), x2='pos_limit:Q')
        )

        center_spine = (
            alt.Chart(pd.DataFrame({'x': [0]}))
            .mark_rule(color='black', strokeWidth=2, tooltip=None)
            .encode(x='x:Q')
        )

        rel_rules = (
            base_rel.transform_filter('datum.character == datum.dominant_char')
            .mark_rule(size=4)
            .encode(
                x=alt.X('diff:Q', title='Word Count Difference'),
                x2=alt.datum(0),
                y=alt.Y('number_in_season:O', title='Episode Number in Season'),
                color=alt.Color('character:N',
                                scale=alt.Scale(range=['#f40c0c', '#0e33eb']),
                                legend=None),
                opacity=alt.condition(episode_selector, alt.value(1), alt.value(0.1)),
                tooltip=[
                    alt.Tooltip('number_in_season:O', title='Episode'),
                    alt.Tooltip('character:N', title='Dominant Character'),
                    alt.Tooltip('abs_diff:Q', title='Word Difference')
                ]
            )
        )

        rel_faces = (
            base_rel.transform_filter('datum.character == datum.dominant_char')
            .mark_image(width=30, height=30)
            .encode(
                x='diff:Q',
                y='number_in_season:O',
                url='image:N',
                opacity=alt.condition(episode_selector, alt.value(1), alt.value(0.4))
            )
        )

        q3 = (symmetry_fix + center_spine + rel_rules + rel_faces).properties(
            width=400,
            height=600,
            title='Relative Advantage'
        ).add_params(episode_selector, season_selector, char1_selector, char2_selector)

    # --- Q4: cumulative word count within episode ---

    x_scale = alt.Scale(zero=False, nice=False, padding=0)
    y_scale = alt.Scale(zero=True)

    base = (
        alt.Chart(data_q4)
        .transform_filter(episode_selector)
        .transform_filter(season_selector)
        .transform_filter(char1_selector | char2_selector)
        .transform_window(
            cumulative_words='sum(word_count)',
            sort=[alt.SortField('line_number_in_episode')],
            groupby=['character']
        )
        .transform_joinaggregate(max_line_number='max(line_number_in_episode)')
    )

    domain_anchor = (
        alt.Chart(data_q4)
        .transform_filter(episode_selector)
        .transform_filter(season_selector)
        .transform_filter(char1_selector | char2_selector)
        .transform_joinaggregate(max_line_number='max(line_number_in_episode)')
        .transform_calculate(x0='0', x1='datum.max_line_number')
        .mark_rule(opacity=0)
        .encode(x=alt.X('x0:Q', scale=x_scale), x2='x1:Q')
    )

    highlight_lines = (
        base
        .mark_line(strokeWidth=2, point=True)
        .transform_filter(char1_selector | char2_selector)
        .encode(
            x=alt.X('line_number_in_episode:Q', title='Line Number in Episode', scale=x_scale),
            y=alt.Y('cumulative_words:Q', title='Cumulative Words Spoken', scale=y_scale),
            color=alt.Color('character:N', legend=None,
                            scale=alt.Scale(range=['#0e33eb', '#f40c0c'])),
            tooltip=[
                alt.Tooltip('character:N'),
                alt.Tooltip('line_number_in_episode:Q'),
                alt.Tooltip('cumulative_words:Q', title='Total Words Spoken')
            ]
        )
    )

    faces_q4 = (
        base
        .transform_filter(char1_selector | char2_selector)
        .transform_window(
            rank='rank()',
            sort=[alt.SortField('line_number_in_episode', order='descending')],
            groupby=['character']
        )
        .transform_filter(alt.datum.rank == 1)
        .mark_image(width=30, height=30, clip=False)
        .encode(
            x=alt.value(620),
            y=alt.Y('cumulative_words:Q', scale=y_scale),
            url='image:N'
        )
    )

    q4 = (domain_anchor + highlight_lines + faces_q4).properties(
        width=600,
        height=600,
        title='Cumulative Word Count'
    )

    # --- Final assembly ---
    # No add_params here — all params are registered on their own views above,
    # exactly as in the working reference script.
    final_chart = alt.hconcat(
        selection_ui, q3, q4, heatmap_seasons
    ).resolve_scale(
        y='independent'
    ).configure_view(stroke=None)

    return final_chart


@st.cache_data
def load_data_q3():
    return pd.read_csv('../data/data_Q3.csv')


@st.cache_data
def load_data_q4():
    return pd.read_csv('../data/data_Q4.csv')


@st.cache_resource
def create_plot_q4_html(view):
    df_q3 = load_data_q3()
    df_q4 = load_data_q4()
    chart = create_episode_comparison_plot(df_q3, df_q4, type=view)
    return chart.to_html()