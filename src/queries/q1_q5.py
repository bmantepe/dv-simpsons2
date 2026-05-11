import streamlit as st
import pandas as pd
import altair as alt

# Enable VegaFusion for larger datasets
alt.data_transformers.enable("vegafusion")

def create_character_plot(filter_type: str, df_agg: pd.DataFrame, df_dist: pd.DataFrame):
    """
    Generates a horizontally concatenated Altair chart based on the metric type.
    Includes cross-filtering where selecting a bar filters the distribution plot.
    """
    
    # 1. Detect filter type and set dynamic variables
    if filter_type.lower() == 'word':
        col_name = "word_count"
        metric_label = "Word"
    elif filter_type.lower() == 'sentence':
        col_name = "sentence_count"
        metric_label = "Sentence"
    else:
        raise ValueError("filter_type must be either 'word' or 'sentence'")

    # 2. Base Encodings & Selections
    sort_order = df_agg['character'].tolist()
    
    y_enc = alt.Y(
        "character:N",
        sort=sort_order,
        axis=alt.Axis(domain=False, ticks=False, labels=False, title=None)
    )

    # Altair Selection for cross-filtering
    selector = alt.selection_point(fields=['character'])

    # 3. Bar Chart (Aggregated Data)
    bars = alt.Chart(df_agg).mark_bar().encode(
        x=alt.X(f"{col_name}:Q", title=f"Total {metric_label} Count"),
        y=y_enc,
        tooltip=[
            alt.Tooltip("character:N", title="Character"), 
            alt.Tooltip(f"{col_name}:Q", title=f"Total {metric_label} Count")
        ],
        # Dim unselected bars
        opacity=alt.when(selector).then(alt.value(1)).otherwise(alt.value(0.2))
    ).add_params(selector)

    flags = (
        alt.Chart(df_agg.assign(zero=0))
        .mark_image(width=25, height=25, clip=False, xOffset=-12)
        .encode(
            y=y_enc,
            x=alt.X("zero:Q"),
            url="image:N"
        )
    )
    
    barplot_final = (bars + flags).properties(
        width=750, 
        title=f"Total {metric_label} Count per Character"
    )

    # 4. Jitter Plot (Distribution Data) - WITH ALTAIR FILTER
    gaussian_jitter = alt.Chart(df_dist, title=f'{metric_label} Count Distribution').mark_circle(size=8).encode(
        y=y_enc,
        x=alt.X(f"{col_name}:Q", title=f"{metric_label} Count"),
        yOffset="jitter:Q",
        # Added color for better visual distinction when filtered
        #color=alt.Color("character:N", legend=None) 
    ).transform_calculate(
        jitter="sqrt(-2*log(random()))*cos(2*PI*random())"
    ).transform_filter(
        selector # ALTAIR FILTER: Only show distribution for selected character(s)
    )

    mean_bar = alt.Chart(df_dist).mark_tick(
        color='red', size=30, thickness=3
    ).transform_aggregate(
        mean_val=f"mean({col_name})",
        groupby=["character"]
    ).encode(
        x=alt.X("mean_val:Q"),
        y=y_enc
    ).transform_filter(
        selector # ALTAIR FILTER: Only show mean line for selected character(s)
    )
    
    jitter_final = (gaussian_jitter + mean_bar).properties(width=750)

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

# Streamlit Native Filter for Metric Type
selected_filter = st.radio(
    "Select Analysis Metric:", 
    ["Word", "Sentence"], 
    horizontal=True
)


# 2. Data Loading
@st.cache_data
def load_data_q1_q5():
    characters = ['Homer', 'Bart', 'Lisa', 'Marge', 'Apu']
    
    q1_1 = pd.read_csv('../data/data_Q1-1.csv')
    q1_2 = pd.read_csv('../data/data_Q1-2.csv')
    q5_1 = pd.read_csv('../data/data_Q5-1.csv')
    q5_2 = pd.read_csv('../data/data_Q5-2.csv')
    
    # Pre-filter the dataframes
    q1_1 = q1_1[q1_1['character'].isin(characters)]
    q1_2 = q1_2[q1_2['character'].isin(characters)]
    q5_1 = q5_1[q5_1['character'].isin(characters)]
    q5_2 = q5_2[q5_2['character'].isin(characters)]
    
    return q1_1, q1_2, q5_1, q5_2

data_q1_1, data_q1_2, data_q5_1, data_q5_2 = load_data_q1_q5()

# 3. Route the data to the function based on the selection
if selected_filter == "Word":
    chart = create_character_plot("word", data_q1_1, data_q1_2)
else:
    chart = create_character_plot("sentence", data_q5_1, data_q5_2)

# 4. Render in Streamlit
st.altair_chart(chart, use_container_width=True)