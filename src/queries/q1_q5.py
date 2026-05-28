import streamlit as st
import pandas as pd
import altair as alt

alt.data_transformers.enable("vegafusion")

def create_character_plot(df_agg: pd.DataFrame, df_dist: pd.DataFrame):
    """
    Generates a horizontally concatenated Altair chart.
    Uses native Altair bindings to switch between metrics instantly without 
    triggering a Streamlit backend rerun.
    """
    # Base Encodings
    sort_order = df_agg['character'].unique().tolist()
    
    y_enc = alt.Y(
        "character:N",
        sort=sort_order,
        axis=alt.Axis(domain=False, ticks=False, labels=False, title=None)
    )

    # 1. ALTAIR NATIVE FILTER: Map the underlying data to the UI labels
    metric_dropdown = alt.binding_radio(
        options=['word_count', 'sentence_count'], # The actual values in your CSV
        labels=['Word', 'Sentence'],              # What the user sees in the UI
        name='Analysis Metric: '
    )
    metric_selector = alt.selection_point(
        fields=['count_type'], 
        bind=metric_dropdown, 
        value=[{'count_type': 'word_count'}] # FIX: Wrapped the dictionary in a list []
    )

    # 2. CHARACTER SELECTION: Set default selected characters
    default_chars = [
        {"character": "Apu"}, 
        {"character": "Bart"}, 
        {"character": "Lisa"}, 
        {"character": "Homer"}, 
        {"character": "Marge"}
    ]
    char_selector = alt.selection_point(fields=['character'], value=default_chars)

    # 3. Bar Chart (Aggregated Data)
    bars = alt.Chart(df_agg).mark_bar().encode(
        x=alt.X("count:Q", title="Total Count"), # Updated from value:Q to count:Q
        y=y_enc,
        tooltip=[
            alt.Tooltip("character:N", title="Character"), 
            alt.Tooltip("count:Q", title="Total Count"),
            alt.Tooltip("count_type:N", title="Count Type")
        ],
        opacity=alt.when(char_selector).then(alt.value(1)).otherwise(alt.value(0.2))
    ).add_params(
        char_selector, 
        metric_selector
    ).transform_filter(
        metric_selector 
    )

    flags = alt.Chart(df_agg).mark_image(width=25, height=25, clip=False, xOffset=-12).encode(
        y=y_enc,
        x=alt.value(0), 
        url="image:N"
    ).transform_filter(
        metric_selector
    )
    
    barplot_final = (bars + flags).properties(
        width=300, 
        title="Total Dialogue Count"
    )

    # 4. Jitter Plot (Distribution Data)
    gaussian_jitter = alt.Chart(df_dist, title='Dialogue Distribution').mark_circle(size=8).encode(
        y=y_enc,
        x=alt.X("count:Q", title="Count"), # Updated from value:Q to count:Q
        yOffset="jitter:Q",
        opacity=alt.when(char_selector).then(alt.value(0.8)).otherwise(alt.value(0.2))
    ).transform_calculate(
        jitter="sqrt(-2*log(random()))*cos(2*PI*random())"
    ).add_params(
        char_selector,
        metric_selector 
    ).transform_filter(
        metric_selector 
    )

    mean_bar = alt.Chart(df_dist).mark_tick(
        color='red', size=30, thickness=3
    ).transform_aggregate(
        mean_val="mean(count)",               # Updated from mean(value)
        groupby=["character", "count_type"]   # Updated from metric to count_type
    ).encode(
        x=alt.X("mean_val:Q"),
        y=y_enc
    ).transform_filter(
        metric_selector 
    )
    
    jitter_final = (gaussian_jitter + mean_bar).properties(width=300)

    # 5. Concatenate and Return
    final_layout = alt.hconcat(
        barplot_final, 
        jitter_final
    ).configure_view(
        step=40 
    ).resolve_scale(
        y='shared' 
    )

    return final_layout

# ==========================================
# STREAMLIT APP DASHBOARD
# ==========================================

st.set_page_config(layout="wide", page_title="The Simpsons Dialogue")

# 1. App setup and filter selection
st.title("The Simpsons: Character Dialogue Analysis")
st.markdown("Click on a character's bar on the left to **filter** their specific dialogue distribution on the right. Shift-click to select multiple characters.")

# 2. Data Loading
@st.cache_data
def load_data_q1_q5():    
    q1_q5 = pd.read_csv('../data/data_Q1_Q5.csv')
    # Create aggregated dataframe for the bar chart (aggregate by character and count_type)
    q1_q5_agg = q1_q5.groupby(['character', 'count_type', 'image'], as_index=False)['count'].sum()
    return q1_q5, q1_q5_agg

data_q1_q5, data_q1_q5_agg = load_data_q1_q5()

# --- NEW: Streamlit Multiselect for 5 Characters Max ---
all_characters = sorted(data_q1_q5_agg['character'].unique().tolist())
default_5_chars = ["Apu", "Bart", "Homer", "Lisa", "Marge"]

selected_chars = st.multiselect(
    "Select Characters (Max 5):",
    options=all_characters,
    default=default_5_chars,
    max_selections=5 # <--- This natively enforces the maximum 5 rule!
)

# Stop the app from rendering an empty chart if the user clears all characters
if not selected_chars:
    st.info("Please select at least one character to view the chart.")
else:
    # Filter the dataframes to ONLY contain the selected characters
    filtered_agg = data_q1_q5_agg[data_q1_q5_agg['character'].isin(selected_chars)]
    filtered_dist = data_q1_q5[data_q1_q5['character'].isin(selected_chars)]

    # Generate the chart using the filtered data
    chart = create_character_plot(df_agg=filtered_agg, df_dist=filtered_dist) 

    # Render in Streamlit
    st.altair_chart(chart, use_container_width=True)