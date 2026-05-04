import streamlit as st
import pandas as pd
import altair as alt

# Enable VegaFusion for larger datasets
alt.data_transformers.enable("vegafusion")

def create_timeline_plot(df: pd.DataFrame):
    """
    Generates an interactive line chart tracking word count over seasons.
    Features hover tooltips, vertical rules, and character images.
    """
    # Fix the Y-axis domain based on the maximum value of the currently selected data
    max_y = df['word_count'].max()
    # Handle edge case where dataframe might be empty
    if pd.isna(max_y): 
        max_y = 100

    # 1. Selections
    # Fixed typo from 'nearrest' to 'nearest'
    nearest = alt.selection_point(nearest=True, on='mouseover', fields=['season'], empty=False)
    legend_selection = alt.selection_point(fields=['character'], bind='legend')

    # 2. Invisible selectors for the hover effect
    selectors = alt.Chart(df).mark_point().encode(
        x='season:O',
        opacity=alt.value(0),
    ).add_params(nearest)  

    # 3. Main Line Chart
    lines_main = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X('season:O', title='Season'),
        y=alt.Y('word_count:Q', title='Total Word Count', scale=alt.Scale(domain=(0, max_y))),
        color=alt.Color('character:N', legend=alt.Legend(title="Character")),
        # Dim lines if another character is clicked in the legend
        opacity=alt.when(legend_selection).then(alt.value(1)).otherwise(alt.value(0.2))
    ).add_params(nearest, legend_selection)

    # 4. Tooltip Text (Appears on hover)
    text = lines_main.mark_text(align='left', dx=10, dy=-15).encode(
        text=alt.condition(nearest, 'word_count:N', alt.value(''))
    )

    # 5. Character Images (Appears on hover)
    images_point = alt.Chart(df).mark_image(
        width=30, height=30, align='center', baseline='middle'
    ).encode(
        x='season:O',
        y='word_count:Q',
        url='image:N'
    ).transform_filter(
        nearest
    )

    # 6. Vertical Rule (Appears on hover)
    rules = alt.Chart(df).mark_rule(color='gray').encode(
        x='season:O',
    ).transform_filter(
        nearest
    )

    # 7. Layer everything together
    chart = alt.layer(
        selectors, lines_main, text, rules, images_point
    ).properties(
        height=400,
        title='Total Word Count per Season for Selected Characters'
    ).configure_axisX(
        labelAngle=0
    )

    return chart

# ==========================================
# STREAMLIT APP DASHBOARD
# ==========================================

st.set_page_config(layout="wide", page_title="The Simpsons Timeline")

st.title("The Simpsons: Dialogue Timeline Analysis")
st.markdown("Select characters from the dropdown below to track their word counts over the seasons. Hover over the points to see specific values and character images.")

# 1. Data Loading
@st.cache_data
def load_data_q2():
    return pd.read_csv('../data/data_line_plot.csv')

df_full = load_data_q2()

# 2. Extract unique characters for the multiselect filter
# Sorting them alphabetically makes it easier for users to find characters
all_characters = sorted(df_full['character'].unique().tolist())

# Default characters to show when the app loads
default_chars = ['Homer', 'Marge', 'Bart']

# 3. Streamlit Multiselect Filter
selected_chars = st.multiselect(
    "Select Characters to Display:", 
    options=all_characters, 
    default=default_chars
)

st.divider()

# 4. Render the Plot
if not selected_chars:
    st.info("Please select at least one character from the dropdown menu above.")
else:
    # Filter the dataframe based on the user's multiselect choice
    data_filtered = df_full[df_full['character'].isin(selected_chars)]
    
    # Generate and display the chart
    timeline_chart = create_timeline_plot(data_filtered)
    st.altair_chart(timeline_chart, use_container_width=True)