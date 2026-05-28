import pandas as pd
import altair as alt
import streamlit as st

# Enable VegaFusion for larger datasets
alt.data_transformers.enable("vegafusion")

def create_episode_comparison_plot2(data_q3,data_q4, type):

    season_df =pd.DataFrame({
    'season': data_q3['season'].unique(),
    'value': [1] * len(data_q3['season'].unique())
})

    # season selector

    season_selector = alt.selection_point(fields=['season'],value=1,name = 'season_selector')
    heatmap_seasons = alt.Chart(season_df).mark_rect().encode(
        y=alt.Y('season:O', title='Season'),
        color= alt.Color('value:Q', legend=None),
        opacity=alt.when(season_selector).then(alt.value(1)).otherwise(alt.value(0.4)),
    )

    # selection of characters

    char1_selector = alt.selection_point(fields=['character'],name = 'char1_selector',value = 'Bart')
    char2_selector = alt.selection_point(fields=['character'],name = 'char2_selector',value = 'Lisa')
    all_characters = sorted(data_q3['character'].unique().tolist())
    y_scale = alt.Scale(domain=all_characters)


    char1_base = alt.Chart(data_q3)

    heatmap1 = char1_base.mark_rect(color='#0e33eb').encode(
        y=alt.Y('character:N', scale=y_scale, title='Select Character 1'),
        opacity=alt.condition(char1_selector, alt.value(1), alt.value(0))
    )

    faces1 = char1_base.mark_image(size=400).encode(
        y=alt.Y('character:N', scale=y_scale, axis=alt.Axis(labels=False, ticks=False, title=None)),
        url="image:N"
    )

    char2_base = alt.Chart(data_q3)

    heatmap2 = char2_base.mark_rect(color='#f40c0c').encode(
        y=alt.Y('character:N', scale=y_scale, title='Select Character 2'),
        opacity=alt.condition(char2_selector, alt.value(1), alt.value(0))
    )

    faces2 = char2_base.mark_image(size=400).encode(
        y=alt.Y('character:N', scale=y_scale, axis=alt.Axis(labels=False, ticks=False, title=None)),
        url="image:N"
    )

    selection_ui = alt.hconcat(
    (heatmap1 + faces1), 
    (heatmap2 + faces2)
    ).resolve_scale(
        y='shared'
    )  
    
    #epsiode selector 
    episode_selector = alt.selection_point(fields=['episode_id'],on = 'mouseover')


    # q3 abosluite scale 

    if type == "Absolute":

        chart = (
            alt.Chart(data_q3).transform_filter(char1_selector | char2_selector).transform_joinaggregate(max_row='argmax(word_count)', groupby=['season', 'number_in_season']
            ).transform_calculate(
                more_words= 'datum.max_row.character'
            ).encode(
                x=alt.X("word_count:Q", title="Word Count"),
                y=alt.Y("number_in_season:O", title="Episode Number in Season"),
                detail="number_in_season:O",
                tooltip=["season:O", "number_in_season:O", "character:N", "word_count:Q"],
                color=alt.Color('more_words:N', title='More Words', legend=None,scale=alt.Scale(range=['#0e33eb', '#f40c0c'])),
                opacity=alt.condition(episode_selector, alt.value(1), alt.value(0.2))
            ).transform_filter(
                season_selector
            )
        )



        line = chart.mark_line(strokeWidth=4)

        faces = chart.mark_image(width=20, height=20).encode(
            url="image:N",

        )

        points = chart.mark_point(size=500, filled=True).encode(
            color = alt.Color('character:N', title='Character')
        )

        #dynamic_title = alt.Title(alt.expr(f'"Difference " + {select_x.name}.level_0 + " - " + {select_y.name}.level_1'))
        dynamic_title = alt.Title(
            text=alt.expr(
                f"{char1_selector.name}.character + ' vs ' + "
                f"{char2_selector.name}.character + "
                f"' Word Count by Episode (Season ' + toString({season_selector.name}.season) + ')'"
            )
        )
        q3 =(line + points + faces).properties(
            title=dynamic_title,
            width=600,
            height=600
        )

    else: 

        base_rel = alt.Chart(data_q3).transform_filter(
            season_selector & (char1_selector | char2_selector)
        ).transform_calculate(
            c1_val = f"datum.character == {char1_selector.name}.character ? datum.word_count : 0",
            c2_val = f"datum.character == {char2_selector.name}.character ? datum.word_count : 0"
        ).transform_joinaggregate(
            sum_c1 = 'sum(c1_val)',
            sum_c2 = 'sum(c2_val)',
            groupby=['episode_id']
        ).transform_calculate(
            diff = "datum.sum_c2 - datum.sum_c1",
            abs_diff = "abs(datum.diff)",
            dominant_char = f"datum.diff > 0 ? {char2_selector.name}.character : {char1_selector.name}.character"
        )

        symmetry_fix = base_rel.transform_aggregate(
            max_abs='max(abs_diff)'
        ).transform_calculate(
            neg_limit='-datum.max_abs',
            pos_limit='datum.max_abs'
        ).mark_rule(opacity=0, tooltip=None).encode( # <--- tooltip=None is key
            x=alt.X('neg_limit:Q'),
            x2='pos_limit:Q'
        )

        # 2. The Center Spine (Also non-interactive)
        center_spine = alt.Chart(pd.DataFrame({'x': [0]})).mark_rule(
            color='black', strokeWidth=2, tooltip=None # <--- tooltip=None is key
        ).encode(x='x:Q')

        # 3. The Mirror Rules (The PRIMARY TRIGGER)
        rel_rules = base_rel.transform_filter("datum.character == datum.dominant_char").mark_rule(size=4).encode(
            x=alt.X('diff:Q', title="Word Count Difference"),
            x2=alt.datum(0), 
            y=alt.Y('number_in_season:O', title='Episode Number in Season'),
            color=alt.Color('character:N', 
                            scale=alt.Scale( range=['#f40c0c', '#0e33eb']), 
                            legend=None),
            opacity=alt.condition(episode_selector, alt.value(1), alt.value(0.1)),
            tooltip=[
                alt.Tooltip('number_in_season:O', title='Episode'),
                alt.Tooltip('character:N', title='Dominant Character'),
                alt.Tooltip('abs_diff:Q', title='Word Difference')
            ]
        )

        # 4. The Faces (Also interactive)
        rel_faces = base_rel.transform_filter("datum.character == datum.dominant_char").mark_image(width=30, height=30).encode(
            x='diff:Q',
            y='number_in_season:O',
            url='image:N',
            # Ensure faces also respond to the selector
            opacity=alt.condition(episode_selector, alt.value(1), alt.value(0.4))
        )

        # --- COMBINE IN CORRECT LAYER ORDER ---
        # Put background elements FIRST, interactive data LAST (so they are on top)
        q3 = (symmetry_fix + center_spine + rel_rules + rel_faces).properties(
            width=600,
            height=600,
            title="Relative Advantage"
        )

        # CRITICAL: Always add params to the final object
        # If this is part of a larger dashboard, add it to the final concat object!
    

    x_scale = alt.Scale(zero=False, nice=False, padding=0)
    y_scale = alt.Scale(zero=True)

    # Base transformed data
    base = (
        alt.Chart(data_q4)
        .transform_filter(episode_selector,season_selector,char1_selector | char2_selector)
        .transform_window(
            cumulative_words='sum(word_count)',
            sort=[alt.SortField('line_number_in_episode')],
            groupby=['character']
        )
        .transform_joinaggregate(
            max_line_number='max(line_number_in_episode)'
        )
    )

    domain_anchor = (
        alt.Chart(data_q4)
        .transform_filter(episode_selector,season_selector,char1_selector | char2_selector)
        .transform_joinaggregate(
            max_line_number='max(line_number_in_episode)'
        )
        .transform_calculate(
            x0='0',
            x1='datum.max_line_number'
        )
        .mark_rule(opacity=0)
        .encode(
            x=alt.X('x0:Q', scale=x_scale),
            x2='x1:Q'
        )
    )

    highlight_lines = (
        base
        .mark_line(strokeWidth=2, point=True)
        .transform_filter(char1_selector | char2_selector )
        ).encode(
            x=alt.X(
                'line_number_in_episode:Q',
                title='Line Number in Episode',
                scale=x_scale
            ),
            y=alt.Y(
                'cumulative_words:Q',
                title='Cumulative Words Spoken',
                scale=y_scale
            ),
            color=alt.Color('character:N', legend=None,scale = alt.Scale(range=['#0e33eb', '#f40c0c'])),
            tooltip=[
                alt.Tooltip('character:N'),
                alt.Tooltip('line_number_in_episode:Q'),
                alt.Tooltip('cumulative_words:Q', title='Total Words Spoken')
            ]
        )

    faces = (
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
            x=alt.value(620),   # chart width (600) + 20px outside plot box
            y=alt.Y('cumulative_words:Q', scale=y_scale),
            url='image:N'
        )
    )

    q4 = (
        (domain_anchor + highlight_lines + faces)
        .properties(
            width=600,
            height=600,
            title="Cumulative Word Count"
        )
    )

    final_chart = alt.hconcat(
        selection_ui, q3.properties(width=400, height=600), q4, heatmap_seasons
    ).resolve_scale(
        y='independent'
    ).add_params(
        season_selector, char1_selector, char2_selector, episode_selector
    ).configure_view(stroke=None)

    return final_chart



@st.cache_data
def load_data_q32():
    df_q3 = pd.read_csv('../data/data_Q3.csv') 
    return df_q3

@st.cache_data
def load_data_q42():
    df_q4 = pd.read_csv('../data/data_Q4.csv') 
    return df_q4