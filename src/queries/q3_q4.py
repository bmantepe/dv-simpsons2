import streamlit as st
import pandas as pd
import altair as alt

alt.data_transformers.disable_max_rows()


def create_episode_comparison_plot(data_q3, data_q4, type):

    season_df = pd.DataFrame({
        'season': data_q3['season'].unique(),
        'value': [1] * len(data_q3['season'].unique())
    })

    # --- Selectors & Hover Trackers ---

    season_selector = alt.selection_point(fields=['season'], value=1, name='season_selector')
    char1_selector = alt.selection_point(fields=['character'], name='char1_selector', value='Bart')
    char2_selector = alt.selection_point(fields=['character'], name='char2_selector', value='Lisa')
    episode_selector = alt.selection_point(fields=['episode_id'], on='mouseover', name='episode_selector')
    
    hover1 = alt.selection_point(on='mouseover', clear='mouseout', empty=False)
    hover2 = alt.selection_point(on='mouseover', clear='mouseout', empty=False)

    # --- Season heatmap (HORIZONTAL AT THE TOP) ---

    # 1. Create an invisible spacer to push the heatmap to the right
    spacer = alt.Chart(pd.DataFrame({'empty': [1]})).mark_rect(opacity=0).properties(
        width=180, # Matches the width of Char1 (50) + Char2 (50) + spacing (20)
        height=40
    )

    # 2. Make the heatmap slightly narrower since the spacer is taking up 120px
    heatmap_seasons = alt.Chart(season_df).mark_rect().encode(
        x=alt.X('season:O', title='Select Season', axis=alt.Axis(labelAngle=0, orient='top', tickSize=0)),
        color=alt.Color('value:Q', legend=None),
        opacity=alt.when(season_selector).then(alt.value(1)).otherwise(alt.value(0.4)),
    ).properties(
        width=1380,    # 1500 total width - 120 spacer = 1380
        height=40
    ).add_params(season_selector)
    
    # 3. Combine them horizontally to form the top row
    top_row = alt.hconcat(spacer, heatmap_seasons)

    # --- Character 1 Selector UI (BLUE) ---

    char1_base = alt.Chart(data_q3)

    heatmap1 = char1_base.mark_rect(cornerRadius=8).encode(
        # Removed the hacked Y-axis title
        y=alt.Y('character:N', axis=alt.Axis(labels=False, ticks=False, domain=False, title=None)),
        
        color=alt.when(char1_selector).then(alt.value('rgba(14, 51, 235, 0.15)')) 
             .when(hover1).then(alt.value('rgba(117, 104, 104, 0.2)'))
             .otherwise(alt.value('transparent')),
        
        stroke=alt.when(char1_selector).then(alt.value('#0e33eb'))
               .when(hover1).then(alt.value('#4c78a8'))
               .otherwise(alt.value('#756868')),
               
        strokeWidth=alt.when(char1_selector).then(alt.value(3))
                    .when(hover1).then(alt.value(2))
                    .otherwise(alt.value(1))
    ).add_params(char1_selector, hover1)

    faces1 = char1_base.mark_image(width=30, height=30, xOffset=-25).encode(
        y=alt.Y('character:N', axis=alt.Axis(labels=False, ticks=False, title=None)),
        url='image:N'
    )

    # FIX: Native Altair Title, color-coded and centered. Height reduced to 450.
    char1_ui = (heatmap1 + faces1).properties(
        width=50, 
        height=450,
        title=alt.TitleParams('Character 1', color='#0e33eb', align='center', anchor='middle', fontSize=13)
    )

    # --- Character 2 Selector UI (RED) ---

    char2_base = alt.Chart(data_q3)

    heatmap2 = char2_base.mark_rect(cornerRadius=8).encode(
        # Removed the hacked Y-axis title
        y=alt.Y('character:N', axis=alt.Axis(labels=False, ticks=False, domain=False, title=None)),
        
        color=alt.when(char2_selector).then(alt.value('rgba(244, 12, 12, 0.15)')) 
             .when(hover2).then(alt.value('rgba(117, 104, 104, 0.2)'))
             .otherwise(alt.value('transparent')),
        
        stroke=alt.when(char2_selector).then(alt.value('#f40c0c'))
               .when(hover2).then(alt.value('#e06666'))
               .otherwise(alt.value('#756868')),
               
        strokeWidth=alt.when(char2_selector).then(alt.value(3))
                    .when(hover2).then(alt.value(2))
                    .otherwise(alt.value(1))
    ).add_params(char2_selector, hover2)

    faces2 = char2_base.mark_image(width=30, height=30, xOffset=-25).encode(
        y=alt.Y('character:N', axis=alt.Axis(labels=False, ticks=False, title=None)),
        url='image:N'
    )
    
    # FIX: Native Altair Title, color-coded and centered. Height reduced to 450.
    char2_ui = (heatmap2 + faces2).properties(
        width=50, 
        height=450,
        title=alt.TitleParams('Character 2', color='#f40c0c', align='center', anchor='middle', fontSize=13)
    )

    selection_ui = alt.hconcat(
        char1_ui,
        char2_ui
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
            width=550,     
            height=450     # DECREASED HEIGHT TO 450
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
            width=550,     
            height=450,    # DECREASED HEIGHT TO 450
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
            x=alt.value(770), 
            y=alt.Y('cumulative_words:Q', scale=y_scale),
            url='image:N'
        )
    )

    q4 = (domain_anchor + highlight_lines + faces_q4).properties(
        width=750,      
        height=450,     # DECREASED HEIGHT TO 450
        title='Cumulative Word Count'
    )

    # --- Final assembly ---
    
    bottom_row = alt.hconcat(
        selection_ui, q3, q4
    ).resolve_scale(
        y='independent'
    )

    final_chart = alt.vconcat(
        top_row,
        bottom_row
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