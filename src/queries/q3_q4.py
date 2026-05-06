import pandas as pd
import altair as alt
import streamlit as st

# Enable VegaFusion for larger datasets
alt.data_transformers.enable("vegafusion")

def create_episode_comparison_plot(df: pd.DataFrame, season: int, characters: list):
    # Create a dynamic title based on the selected characters and season
    if len(characters) == 2:
        char_title = f"{characters[0]} vs {characters[1]}"
    elif len(characters) == 1:
        char_title = f"{characters[0]}'s"
    else:
        char_title = "Selected Characters"
        
    chart_title = f"{char_title} Word Count by Episode (Season {season})"

    # 1. Base chart encoding
    chart = alt.Chart(df).encode(
        x=alt.X("word_count:Q", title="Word Count"),
        y=alt.Y("number_in_season:O", title="Episode Number in Season"),
        detail="number_in_season:O", 
        tooltip=[
            alt.Tooltip("season:O", title="Season"), 
            alt.Tooltip("number_in_season:O", title="Episode"), 
            alt.Tooltip("character:N", title="Character"), 
            alt.Tooltip("word_count:Q", title="Word Count")
        ]
    )

    # 2. Add the connecting line
    line = chart.mark_line(color="#db646f", strokeWidth=4)

    # 3. Add the character images at the points
    faces = chart.mark_image(width=20, height=20).encode(
        url="image:N"
    )

    # 4. Layer them together and configure properties
    final_chart = (line + faces).properties(
        title=chart_title,
        height=500
    )
    
    return final_chart

import pandas as pd
import altair as alt

def create_diverging_difference_plot(df: pd.DataFrame, season: int, characters: list):
    # This plot strictly requires 2 characters
    if len(characters) != 2:
        return alt.Chart(pd.DataFrame({'text': ['Please select exactly 2 characters for the difference plot.']})).mark_text(size=18, color='gray').encode(text='text:N').properties(height=500)

    char1, char2 = characters[0], characters[1]
    
    # Create a mapping of character names to their image URLs
    image_map = dict(zip(df['character'], df['image']))
    
    # Pivot the dataframe to get side-by-side word counts per episode
    df_pivot = df.pivot_table(
        index=['number_in_season', 'season'], 
        columns='character', 
        values='word_count', 
        fill_value=0
    ).reset_index()
    
    # Safety check: ensure both characters exist in the pivot columns
    for char in characters:
        if char not in df_pivot.columns:
            df_pivot[char] = 0

    # Calculate difference (Char2 - Char1)
    df_pivot['diff'] = df_pivot[char2] - df_pivot[char1]
    df_pivot['abs_diff'] = df_pivot['diff'].abs()
    
    # Determine the dominant character and assign their face to the row
    df_pivot['dominant_char'] = df_pivot.apply(lambda row: char2 if row['diff'] > 0 else char1, axis=1)
    df_pivot['image'] = df_pivot['dominant_char'].map(image_map)
    df_pivot['zero'] = 0 
    
    # Determine max axis limit to strictly center the graph at 0
    max_diff = df_pivot['abs_diff'].max()
    limit = (max_diff * 1.15) if not pd.isna(max_diff) and max_diff > 0 else 100 

    # Define the custom color scale (Char1 = Red, Char2 = Blue)
    color_scale = alt.Scale(domain=[char1, char2], range=['#d62728', '#1f77b4'])

    base = alt.Chart(df_pivot).encode(
        y=alt.Y('number_in_season:O', title='Episode Number in Season')
    )
    
    # Apply the dynamic color encoding here
    rule = base.mark_rule(size=3).encode(
        x=alt.X('zero:Q', title=f"← {char1} spoke more  |  {char2} spoke more →", scale=alt.Scale(domain=[-limit, limit])),
        x2='diff:Q',
        color=alt.Color('dominant_char:N', scale=color_scale, legend=None), # Dynamic color
        tooltip=[
            alt.Tooltip('season:O', title='Season'),
            alt.Tooltip('number_in_season:O', title='Episode'),
            alt.Tooltip('dominant_char:N', title='Spoke More By'),
            alt.Tooltip('abs_diff:Q', title='Word Difference')
        ]
    )
    
    face = base.mark_image(width=25, height=25).encode(
        x='diff:Q',
        url='image:N',
        tooltip=[
            alt.Tooltip('season:O', title='Season'),
            alt.Tooltip('number_in_season:O', title='Episode'),
            alt.Tooltip('dominant_char:N', title='Spoke More By'),
            alt.Tooltip('abs_diff:Q', title='Word Difference')
        ]
    )
    
    zero_line = alt.Chart(pd.DataFrame({'x': [0]})).mark_rule(color='black', strokeWidth=1, opacity=0.3).encode(x='x:Q')

    chart_title = f"Word Count Difference: {char1} vs {char2} (Season {season})"
    
    final_chart = (zero_line + rule + face).properties(
        title=chart_title,
        height=500
    )
    
    return final_chart

@st.cache_data
def load_data_q3_q4():
    df_q3 = pd.read_csv('../data/data_Q3.csv') # Make sure this path is correct relative to your run execution!
    return df_q3